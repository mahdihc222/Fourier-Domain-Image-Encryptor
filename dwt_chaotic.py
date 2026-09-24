"""Multilevel Haar DWT encryption with logistic-map-based coefficient permutation."""

import hashlib

import numpy as np
from PIL import Image, PngImagePlugin


class DWTCiphertext(np.ndarray):
    """NumPy subclass carrying reversible DWT metadata along with the ciphertext."""

    def __new__(cls, values, metadata=None):
        obj = np.asarray(values, dtype=np.float64).view(cls)
        obj.metadata = dict(metadata or {})
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.metadata = getattr(obj, "metadata", {})


def haar_dwt2(image):
    """Compute a single-level 2D Haar DWT with LL, LH, HL, HH layout."""
    array = _validate_image_array(image)
    padded = _pad_to_even(array)
    if padded.ndim == 2:
        return _haar_dwt_channel(padded)

    ll_stack, lh_stack, hl_stack, hh_stack = [], [], [], []
    for channel in range(padded.shape[2]):
        ll, lh, hl, hh = _haar_dwt_channel(padded[:, :, channel])
        ll_stack.append(ll)
        lh_stack.append(lh)
        hl_stack.append(hl)
        hh_stack.append(hh)
    return (
        np.stack(ll_stack, axis=2),
        np.stack(lh_stack, axis=2),
        np.stack(hl_stack, axis=2),
        np.stack(hh_stack, axis=2),
    )


def haar_idwt2(ll, lh, hl, hh):
    """Invert a single-level 2D Haar DWT using the exact pair reconstruction rule."""
    ll = np.asarray(ll, dtype=np.float64)
    lh = np.asarray(lh, dtype=np.float64)
    hl = np.asarray(hl, dtype=np.float64)
    hh = np.asarray(hh, dtype=np.float64)

    if ll.ndim == 2:
        return _haar_idwt_channel(ll, lh, hl, hh)

    restored_stack = []
    for channel in range(ll.shape[2]):
        restored_stack.append(
            _haar_idwt_channel(
                ll[:, :, channel],
                lh[:, :, channel],
                hl[:, :, channel],
                hh[:, :, channel],
            )
        )
    return np.stack(restored_stack, axis=2)


def encrypt(image, key):
    """Apply a two-level Haar DWT and store the packed, permuted coefficient vector as ciphertext."""
    image_array = _validate_image_array(image)
    original_shape = tuple(image_array.shape)
    padded = _pad_to_even(image_array)

    ll1, lh1, hl1, hh1 = haar_dwt2(padded)
    ll1_even = _pad_to_even(ll1)
    ll2, lh2, hl2, hh2 = haar_dwt2(ll1_even)

    coeffs = _pack_coefficients(ll2, lh2, hl2, hh2, lh1, hl1, hh1)
    permutation = _logistic_permutation(coeffs.size, key, "dwt-coefficients")
    encrypted_data = coeffs[permutation]

    return DWTCiphertext(
        encrypted_data,
        {
            "original_shape": original_shape,
            "key": str(key),
            "shape": encrypted_data.shape,
            "padded_shape": padded.shape,
            "permutation": np.asarray(permutation, dtype=np.int64),
        },
    )


def decrypt(ciphertext, key):
    """Undo the coefficient permutation, unpack the DWT coefficients, and reconstruct the image."""
    array = np.asarray(ciphertext, dtype=np.float64)
    metadata = getattr(ciphertext, "metadata", {}) if hasattr(ciphertext, "metadata") else {}
    original_shape = tuple(metadata.get("original_shape", array.shape))
    padded_shape = tuple(metadata.get("padded_shape", array.shape))
    flat = array.reshape(-1)

    permutation = _logistic_permutation(flat.size, key, "dwt-coefficients")
    inverse = np.argsort(permutation)
    restored = flat[inverse]

    channel_suffix = padded_shape[2:] if len(padded_shape) > 2 else ()
    ll1_shape = (padded_shape[0] // 2, padded_shape[1] // 2) + channel_suffix
    ll1_even_shape = (ll1_shape[0] + (ll1_shape[0] % 2), ll1_shape[1] + (ll1_shape[1] % 2)) + channel_suffix
    ll2_shape = (ll1_even_shape[0] // 2, ll1_even_shape[1] // 2) + channel_suffix
    coefficient_shapes = [
        ll2_shape,
        ll2_shape,
        ll2_shape,
        ll2_shape,
        ll1_shape,
        ll1_shape,
        ll1_shape,
    ]

    ll2, lh2, hl2, hh2, lh1, hl1, hh1 = _unpack_coefficients(restored, coefficient_shapes)
    ll1 = haar_idwt2(ll2, lh2, hl2, hh2)
    ll1 = _trim_padding(ll1, ll1_even_shape[0], ll1_even_shape[1], ll1_shape)
    recovered = haar_idwt2(ll1, lh1, hl1, hh1)
    recovered = _trim_padding(recovered, padded_shape[0], padded_shape[1], original_shape)
    return np.clip(recovered, 0.0, 1.0)


def save_cipher(path, ciphertext):
    """Write a DWT ciphertext to PNG with metadata for a reversible round trip."""
    values = np.asarray(ciphertext, dtype=np.float64)
    flat = values.reshape(-1)
    metadata = getattr(ciphertext, "metadata", {}) if hasattr(ciphertext, "metadata") else {}
    original_shape = tuple(metadata.get("original_shape", values.shape))
    padded_shape = tuple(metadata.get("padded_shape", values.shape))
    low = float(np.min(flat))
    high = float(np.max(flat))
    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError("ciphertext must contain finite values")
    if high == low:
        high = low + 1.0
    values_2d = np.clip((flat - low) / (high - low), 0.0, 1.0).reshape(1, -1)
    quantized = np.rint(values_2d * 65535.0).astype(np.uint16)
    info = PngImagePlugin.PngInfo()
    info.add_text("dwt_original_shape", ",".join(str(value) for value in original_shape))
    info.add_text("dwt_padded_shape", ",".join(str(value) for value in padded_shape))
    info.add_text("dwt_low", repr(low))
    info.add_text("dwt_high", repr(high))
    Image.fromarray(quantized, mode="I;16").save(path, pnginfo=info)


def load_cipher(path):
    """Load a DWT ciphertext written by :func:`save_cipher`."""
    image = Image.open(path)
    info = image.text
    if "dwt_original_shape" not in info or "dwt_low" not in info or "dwt_high" not in info:
        raise ValueError("PNG is missing DWT ciphertext metadata")
    original_shape = tuple(int(value) for value in info["dwt_original_shape"].split(","))
    padded_shape = tuple(int(value) for value in info.get("dwt_padded_shape", "1,1").split(","))
    low = float(info["dwt_low"])
    high = float(info["dwt_high"])
    values = np.asarray(image, dtype=np.float64) / 65535.0
    decoded = values.reshape(-1) * (high - low) + low
    return DWTCiphertext(decoded, {"original_shape": original_shape, "padded_shape": padded_shape})


def _validate_image_array(image):
    array = np.asarray(image, dtype=np.float64)
    if array.ndim not in (2, 3) or (array.ndim == 3 and array.shape[2] not in (1, 3)):
        raise ValueError("image must be grayscale or RGB")
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise ValueError("image must be nonempty and finite")
    return np.clip(array, 0.0, 1.0)


def _pad_to_even(array):
    array = np.asarray(array, dtype=np.float64)
    row_padding = 1 if array.shape[0] % 2 else 0
    col_padding = 1 if array.shape[1] % 2 else 0
    if row_padding == 0 and col_padding == 0:
        return array
    padded = np.zeros((array.shape[0] + row_padding, array.shape[1] + col_padding) + array.shape[2:], dtype=np.float64)
    padded[: array.shape[0], : array.shape[1]] = array
    return padded


def _trim_padding(array, padded_height, padded_width, original_shape):
    if array.shape[:2] != (padded_height, padded_width):
        return array
    height, width = original_shape[:2]
    if array.ndim == 2:
        return array[:height, :width]
    return array[:height, :width, :]


def _haar_dwt_channel(channel):
    """Apply the correct forward Haar DWT using row then column filtering."""
    if channel.shape[0] % 2 == 1 or channel.shape[1] % 2 == 1:
        channel = _pad_to_even(channel)

    row_even = channel[:, 0::2]
    row_odd = channel[:, 1::2]
    horizontal_low = 0.5 * (row_even + row_odd)
    horizontal_high = 0.5 * (row_even - row_odd)

    ll = 0.5 * (horizontal_low[0::2, :] + horizontal_low[1::2, :])
    lh = 0.5 * (horizontal_low[0::2, :] - horizontal_low[1::2, :])
    hl = 0.5 * (horizontal_high[0::2, :] + horizontal_high[1::2, :])
    hh = 0.5 * (horizontal_high[0::2, :] - horizontal_high[1::2, :])
    return ll, lh, hl, hh


def _haar_idwt_channel(ll, lh, hl, hh):
    """Invert a single-channel Haar DWT using the correct separable inverse pair equations."""
    low = np.empty((ll.shape[0] * 2, ll.shape[1]), dtype=np.float64)
    high = np.empty((hl.shape[0] * 2, hl.shape[1]), dtype=np.float64)

    low[0::2, :] = ll + lh
    low[1::2, :] = ll - lh
    high[0::2, :] = hl + hh
    high[1::2, :] = hl - hh

    restored = np.empty((low.shape[0], low.shape[1] * 2), dtype=np.float64)
    restored[:, 0::2] = low + high
    restored[:, 1::2] = low - high
    return restored


def _logistic_sequence(length, key, salt):
    digest = hashlib.sha256(f"{salt}:{key}".encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "little")
    x = (seed % 1_000_000_007) / 1_000_000_007.0
    x = 0.2 + 0.6 * x
    values = np.empty(length, dtype=np.float64)
    for index in range(length + 200):
        x = 3.99 * x * (1.0 - x)
        if index >= 200:
            values[index - 200] = x
    return values


def _logistic_permutation(length, key, salt):
    if length <= 1:
        return np.arange(length, dtype=np.int64)
    return np.argsort(_logistic_sequence(length, key, salt))


def _pack_coefficients(ll2, lh2, hl2, hh2, lh1, hl1, hh1):
    return np.concatenate(
        [
            np.asarray(ll2, dtype=np.float64).ravel(),
            np.asarray(lh2, dtype=np.float64).ravel(),
            np.asarray(hl2, dtype=np.float64).ravel(),
            np.asarray(hh2, dtype=np.float64).ravel(),
            np.asarray(lh1, dtype=np.float64).ravel(),
            np.asarray(hl1, dtype=np.float64).ravel(),
            np.asarray(hh1, dtype=np.float64).ravel(),
        ]
    )


def _unpack_coefficients(flat, shapes):
    index = 0
    outputs = []
    for shape in shapes:
        count = int(np.prod(shape))
        outputs.append(flat[index:index + count].reshape(shape))
        index += count
    return tuple(outputs)


def _permute_subband(subband, key, salt):
    subband = np.asarray(subband, dtype=np.float64)
    flatten = subband.reshape(-1)
    if flatten.size == 0:
        return subband.copy()
    permutation = np.argsort(_logistic_sequence(flatten.size, key, salt))
    return flatten[permutation].reshape(subband.shape)


def _inverse_permute_subband(subband, key, salt):
    subband = np.asarray(subband, dtype=np.float64)
    flatten = subband.reshape(-1)
    if flatten.size == 0:
        return subband.copy()
    permutation = np.argsort(_logistic_sequence(flatten.size, key, salt))
    inverse = np.argsort(permutation)
    return flatten[inverse].reshape(subband.shape)
