import hashlib

import numpy as np
from PIL import Image, PngImagePlugin


class DWTCiphertext(np.ndarray):

    def __new__(cls, values, metadata=None):
        obj = np.asarray(values, dtype=np.float64).view(cls)
        obj.metadata = dict(metadata or {})
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.metadata = getattr(obj, "metadata", {})


def haar_dwt2(image):
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
    image_array = _validate_image_array(image)
    original_shape = tuple(image_array.shape)
    padded = _pad_to_even(image_array)

    ll1, lh1, hl1, hh1 = haar_dwt2(padded)
    ll1_even = _pad_to_even(ll1)
    ll2, lh2, hl2, hh2 = haar_dwt2(ll1_even)

    coeffs = _pack_coefficients(ll2, lh2, hl2, hh2, lh1, hl1, hh1)
    permutation = _logistic_permutation(coeffs.size, key, "dwt-coefficients")
    encrypted_coefficients = coeffs[permutation]
    coefficient_low = float(np.min(encrypted_coefficients))
    coefficient_high = float(np.max(encrypted_coefficients))
    if coefficient_high == coefficient_low:
        coefficient_high = coefficient_low + 1.0
    normalized = np.clip(
        (encrypted_coefficients - coefficient_low) / (coefficient_high - coefficient_low),
        0.0,
        1.0,
    )
    encoded = _encode_rgb_coefficients(normalized)
    rows, columns = _cipher_shape(encoded.size, padded.shape[0], channels=3)
    encrypted_data = np.zeros((rows, columns, 3), dtype=np.float64)
    encrypted_data.reshape(-1)[: encoded.size] = encoded.reshape(-1)

    return DWTCiphertext(
        encrypted_data,
        {
            "original_shape": original_shape,
            "key": str(key),
            "shape": encrypted_data.shape,
            "padded_shape": padded.shape,
            "cipher_shape": encrypted_data.shape,
            "coefficient_count": int(encrypted_coefficients.size),
            "coefficient_low": coefficient_low,
            "coefficient_high": coefficient_high,
            "permutation": np.asarray(permutation, dtype=np.int64),
        },
    )


def encryption_steps(image, key):
    image_array = _validate_image_array(image)
    padded = _pad_to_even(image_array)

    ll1, lh1, hl1, hh1 = haar_dwt2(padded)
    ll1_even = _pad_to_even(ll1)
    ll2, lh2, hl2, hh2 = haar_dwt2(ll1_even)

    coeffs = _pack_coefficients(ll2, lh2, hl2, hh2, lh1, hl1, hh1)
    permutation = _logistic_permutation(coeffs.size, key, "dwt-coefficients")
    permuted = coeffs[permutation]
    coefficient_low = float(np.min(permuted))
    coefficient_high = float(np.max(permuted))
    if coefficient_high == coefficient_low:
        coefficient_high = coefficient_low + 1.0
    normalized = np.clip(
        (permuted - coefficient_low) / (coefficient_high - coefficient_low),
        0.0,
        1.0,
    )
    encoded = _encode_rgb_coefficients(normalized)
    rows, columns = _cipher_shape(encoded.size, padded.shape[0], channels=3)
    ciphertext = np.zeros((rows, columns, 3), dtype=np.float64)
    ciphertext.reshape(-1)[: encoded.size] = encoded.reshape(-1)

    def band_montage(ll, lh, hl, hh):
        return np.concatenate(
            [
                np.concatenate([ll, lh], axis=1),
                np.concatenate([hl, hh], axis=1),
            ],
            axis=0,
        )

    def coefficient_preview(values):
        values = np.asarray(values)
        rows = padded.shape[0]
        columns = int(np.ceil(values.size / rows))
        preview = np.zeros(rows * columns, dtype=values.dtype)
        preview[: values.size] = values
        return preview.reshape(rows, columns)

    return [
        ("Original", image_array),
        ("Level-1 Haar DWT: LL / LH / HL / HH", band_montage(ll1, lh1, hl1, hh1)),
        ("Level-2 Haar DWT of LL1: LL / LH / HL / HH", band_montage(ll2, lh2, hl2, hh2)),
        ("Packed coefficients", coefficient_preview(np.abs(coeffs))),
        ("Normalized coefficient stream (grayscale)", coefficient_preview(normalized)),
        ("24-bit RGB byte-packed ciphertext", ciphertext),
    ]


def decrypt(ciphertext, key):
    array = np.asarray(ciphertext, dtype=np.float64)
    metadata = getattr(ciphertext, "metadata", {}) if hasattr(ciphertext, "metadata") else {}
    original_shape = tuple(metadata.get("original_shape", array.shape))
    padded_shape = tuple(metadata.get("padded_shape", array.shape))
    flat = array.reshape(-1)
    coefficient_count = int(metadata.get("coefficient_count", flat.size))
    if coefficient_count > flat.size:
        raise ValueError("DWT ciphertext is missing coefficient data")
    encoded = flat[: coefficient_count * 3]
    if encoded.size < coefficient_count * 3:
        raise ValueError("DWT ciphertext is missing coefficient data")
    flat = _decode_rgb_coefficients(encoded, coefficient_count)
    if "coefficient_low" in metadata and "coefficient_high" in metadata:
        coefficient_low = float(metadata["coefficient_low"])
        coefficient_high = float(metadata["coefficient_high"])
        flat = flat * (coefficient_high - coefficient_low) + coefficient_low

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


def decryption_steps(ciphertext, key):
    """Return named intermediate arrays for the DWT decryption viewer."""
    array = np.asarray(ciphertext, dtype=np.float64)
    metadata = getattr(ciphertext, "metadata", {}) if hasattr(ciphertext, "metadata") else {}
    original_shape = tuple(metadata.get("original_shape", array.shape))
    padded_shape = tuple(metadata.get("padded_shape", array.shape))
    flat = array.reshape(-1)
    coefficient_count = int(metadata.get("coefficient_count", flat.size))
    if coefficient_count > flat.size:
        raise ValueError("DWT ciphertext is missing coefficient data")
    encoded = flat[: coefficient_count * 3]
    if encoded.size < coefficient_count * 3:
        raise ValueError("DWT ciphertext is missing coefficient data")

    normalized = _decode_rgb_coefficients(encoded, coefficient_count)
    if "coefficient_low" in metadata and "coefficient_high" in metadata:
        coefficient_low = float(metadata["coefficient_low"])
        coefficient_high = float(metadata["coefficient_high"])
        normalized = normalized * (coefficient_high - coefficient_low) + coefficient_low

    permutation = _logistic_permutation(normalized.size, key, "dwt-coefficients")
    restored = normalized[np.argsort(permutation)]

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
    recovered_padded = haar_idwt2(ll1, lh1, hl1, hh1)
    recovered = _trim_padding(recovered_padded, padded_shape[0], padded_shape[1], original_shape)

    def coefficient_preview(values):
        values = np.asarray(values)
        rows = padded_shape[0]
        columns = int(np.ceil(values.size / rows))
        preview = np.zeros(rows * columns, dtype=values.dtype)
        preview[: values.size] = values.ravel()
        return preview.reshape(rows, columns)

    def band_montage(ll, lh, hl, hh):
        bands = np.concatenate(
            [
                np.concatenate([ll, lh], axis=1),
                np.concatenate([hl, hh], axis=1),
            ],
            axis=0,
        )
        minimum = float(np.min(bands))
        maximum = float(np.max(bands))
        if maximum == minimum:
            return np.zeros_like(bands)
        return (bands - minimum) / (maximum - minimum)

    steps = [
        ("Ciphertext", array),
        ("Decoded coefficients", coefficient_preview(np.abs(normalized))),
        ("Inverse logistic permutation", coefficient_preview(np.abs(restored))),
        ("Level-2 bands before inverse Haar DWT", band_montage(ll2, lh2, hl2, hh2)),
        ("Level-1 coefficients reconstructed", np.abs(ll1)),
        ("Recovered image", np.clip(recovered, 0.0, 1.0)),
    ]
    if recovered_padded.shape != recovered.shape:
        steps.insert(-1, ("Inverse Haar DWT before padding crop", np.clip(recovered_padded, 0.0, 1.0)))
    return steps


def save_cipher(path, ciphertext):
    values = np.asarray(ciphertext, dtype=np.float64)
    flat = values.reshape(-1)
    metadata = getattr(ciphertext, "metadata", {}) if hasattr(ciphertext, "metadata") else {}
    original_shape = tuple(metadata.get("original_shape", values.shape))
    padded_shape = tuple(metadata.get("padded_shape", values.shape))
    cipher_shape = tuple(metadata.get("cipher_shape", values.shape))
    coefficient_count = int(metadata.get("coefficient_count", flat.size // 3))
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("DWT ciphertext must be an RGB array")
    if not np.all(np.isfinite(values)):
        raise ValueError("ciphertext must contain finite values")
    quantized = np.rint(np.clip(values, 0.0, 1.0) * 255.0).astype(np.uint8)
    info = PngImagePlugin.PngInfo()
    info.add_text("dwt_original_shape", ",".join(str(value) for value in original_shape))
    info.add_text("dwt_padded_shape", ",".join(str(value) for value in padded_shape))
    info.add_text("dwt_cipher_shape", ",".join(str(value) for value in cipher_shape))
    info.add_text("dwt_coefficient_count", str(coefficient_count))
    info.add_text("dwt_coefficient_low", repr(metadata.get("coefficient_low", 0.0)))
    info.add_text("dwt_coefficient_high", repr(metadata.get("coefficient_high", 1.0)))
    info.add_text("dwt_encoding", "rgb24")
    Image.fromarray(quantized, mode="RGB").save(path, pnginfo=info)


def load_cipher(path):
    image = Image.open(path)
    info = image.text
    if "dwt_original_shape" not in info or "dwt_coefficient_low" not in info or "dwt_coefficient_high" not in info:
        raise ValueError("PNG is missing DWT ciphertext metadata")
    original_shape = tuple(int(value) for value in info["dwt_original_shape"].split(","))
    padded_shape = tuple(int(value) for value in info.get("dwt_padded_shape", "1,1").split(","))
    coefficient_low = float(info["dwt_coefficient_low"])
    coefficient_high = float(info["dwt_coefficient_high"])
    decoded = np.asarray(image, dtype=np.float64) / 255.0
    if "dwt_cipher_shape" in info:
        cipher_shape = tuple(int(value) for value in info["dwt_cipher_shape"].split(","))
        decoded = decoded.reshape(cipher_shape)
    coefficient_count = int(info.get("dwt_coefficient_count", decoded.size))
    return DWTCiphertext(
        decoded,
        {
            "original_shape": original_shape,
            "padded_shape": padded_shape,
            "cipher_shape": tuple(decoded.shape),
            "coefficient_count": coefficient_count,
            "coefficient_low": coefficient_low,
            "coefficient_high": coefficient_high,
        },
    )


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


def _cipher_shape(coefficient_count, height, channels=1):
    rows = max(1, int(height))
    columns = max(1, int(np.ceil(coefficient_count / (rows * channels))))
    return rows, columns


def _encode_rgb_coefficients(values):
    #np.rint rounds to nearest integer, 16777215 = 2^24-1, this line converts normalized float into 24 bit int
    quantized = np.rint(np.clip(values, 0.0, 1.0) * 16777215.0).astype(np.uint32)
    return np.column_stack(
        (
            ((quantized >> 16) & 255),
            ((quantized >> 8) & 255),
            (quantized & 255),
        )
    ).astype(np.float64) / 255.0


def _decode_rgb_coefficients(encoded, coefficient_count):
    bytes_array = np.rint(np.clip(encoded.reshape(coefficient_count, 3), 0.0, 1.0) * 255.0).astype(np.uint32)
    quantized = (bytes_array[:, 0] << 16) | (bytes_array[:, 1] << 8) | bytes_array[:, 2]
    return quantized.astype(np.float64) / 16777215.0


def _trim_padding(array, padded_height, padded_width, original_shape):
    if array.shape[:2] != (padded_height, padded_width):
        return array
    height, width = original_shape[:2]
    if array.ndim == 2:
        return array[:height, :width]
    return array[:height, :width, :]


def _haar_dwt_channel(channel):
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
