"""Arnold-map, DCT, and lightweight diffusion encryption scheme.

The image is scrambled by a reversible Arnold cat map, transformed with an
orthonormal 2-D DCT, diffused with a deterministic XOR keystream, and then
returned through the inverse operations during decryption. The implementation
keeps the original image shape and supports grayscale or RGB arrays.
"""
import hashlib
import ast
from functools import lru_cache
import numpy as np
from PIL import Image, PngImagePlugin


def _validate(image):
    image = np.asarray(image, dtype=np.float64)
    if image.ndim not in (2, 3) or (image.ndim == 3 and image.shape[2] != 3):
        raise ValueError("image must be grayscale or 3-channel RGB")
    if image.size == 0 or not np.all(np.isfinite(image)):
        raise ValueError("image must be nonempty and finite")
    return np.clip(image, 0.0, 1.0)


def _arnold_once(image):
    result = image.copy()
    for row_start, column_start, side in _square_tiles(image.shape[0], image.shape[1]):
        source = image[row_start:row_start + side, column_start:column_start + side]
        rows, columns = np.indices((side, side))
        new_rows = (rows + columns) % side
        new_columns = (rows + 2 * columns) % side
        result[row_start + new_rows, column_start + new_columns] = source
    return result


def _square_tiles(height, width):
    """Yield a complete square tiling, including both-dimensional remainders."""
    pending = [(0, 0, height, width)]
    while pending:
        row_start, column_start, region_height, region_width = pending.pop()
        side = min(region_height, region_width)
        yield row_start, column_start, side
        if region_width > side:
            pending.append((row_start, column_start + side, region_height, region_width - side))
        if region_height > side:
            pending.append((row_start + side, column_start, region_height - side, side))


def arnold_map(image, iterations=1):
    """Apply the Arnold cat map to square tiles covering the full image."""
    result = _validate(image)
    for _ in range(int(iterations) % _arnold_period(result.shape[0], result.shape[1])):
        result = _arnold_once(result)
    return result


def inverse_arnold_map(image, iterations=1):
    """Reverse :func:`arnold_map` using the inverse coordinate mapping."""
    result = np.asarray(image, dtype=np.float64)
    if result.ndim not in (2, 3) or (result.ndim == 3 and result.shape[2] != 3):
        raise ValueError("image must be grayscale or 3-channel RGB")
    if result.size == 0 or not np.all(np.isfinite(result)):
        raise ValueError("image must be nonempty and finite")
    for _ in range(int(iterations) % _arnold_period(result.shape[0], result.shape[1])):
        restored = result.copy()
        for row_start, column_start, side in _square_tiles(result.shape[0], result.shape[1]):
            rows, columns = np.indices((side, side))
            old_rows = (2 * rows - columns) % side
            old_columns = (-rows + columns) % side
            restored[row_start + old_rows, column_start + old_columns] = result[row_start + rows, column_start + columns]
        result = restored
    return result


@lru_cache(maxsize=None)
def _arnold_period(height, width):
    side = min(height, width)
    first_row, first_column = 1 % side, 0
    second_row, second_column = 0, 1 % side
    for period in range(1, side * side * 2 + 1):
        first_row, first_column = (
            (first_row + first_column) % side,
            (first_row + 2 * first_column) % side,
        )
        second_row, second_column = (
            (second_row + second_column) % side,
            (second_row + 2 * second_column) % side,
        )
        if (first_row, first_column) == (1 % side, 0) and (second_row, second_column) == (0, 1 % side):
            return period
    return side * side


def _dct_matrix(size):
    indices = np.arange(size)[:, None]
    frequencies = np.arange(size)[None, :]
    matrix = np.cos(np.pi * (2 * indices + 1) * frequencies / (2 * size))
    matrix[:, 0] *= 1.0 / np.sqrt(2.0)
    return matrix * np.sqrt(2.0 / size)


def _dct2(image):
    rows = _dct_matrix(image.shape[0])
    columns = _dct_matrix(image.shape[1])
    return rows @ image @ columns.T if image.ndim == 2 else np.stack(
        [rows @ image[..., channel] @ columns.T for channel in range(image.shape[2])], axis=2
    )


def _idct2(image):
    rows = _dct_matrix(image.shape[0])
    columns = _dct_matrix(image.shape[1])
    return rows.T @ image @ columns if image.ndim == 2 else np.stack(
        [rows.T @ image[..., channel] @ columns for channel in range(image.shape[2])], axis=2
    )


def _keystream(shape, key):
    seed = hashlib.sha256(str(key).encode("utf-8")).digest()
    seed_value = int.from_bytes(seed[:8], "little")
    return np.random.default_rng(seed_value).integers(0, 65536, size=shape, dtype=np.uint16)


def encrypt(image, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Run Arnold -> DCT -> diffusion and return a float image ciphertext."""
    original = _validate(image)
    scrambled = arnold_map(original, arnold_iterations)
    coefficients = _dct2(scrambled)
    if coefficients.ndim == 3:
        minimum = coefficients.min(axis=(0, 1))
        scale = coefficients.max(axis=(0, 1)) - minimum
        scale = np.where(scale == 0.0, 1.0, scale)
        normalized_values = (coefficients - minimum.reshape(1, 1, -1)) / scale.reshape(1, 1, -1)
        metadata_minimum = minimum.tolist()
        metadata_scale = scale.tolist()
    else:
        minimum, maximum = float(coefficients.min()), float(coefficients.max())
        scale = maximum - minimum or 1.0
        normalized_values = (coefficients - minimum) / scale
        metadata_minimum = minimum
        metadata_scale = scale
    normalized = np.rint(np.clip(normalized_values, 0.0, 1.0) * 65535).astype(np.uint16)
    diffused = np.bitwise_xor(normalized, _keystream(normalized.shape, diffusion_key))
    return diffused.astype(np.float64) / 65535.0, {"minimum": metadata_minimum, "scale": metadata_scale, "shape": original.shape}


def decrypt(ciphertext, metadata, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Reverse diffusion -> IDCT -> inverse Arnold using encryption metadata."""
    encrypted = _validate(ciphertext)
    bytes_data = np.rint(encrypted * 65535.0).astype(np.uint16)
    coefficients = np.bitwise_xor(bytes_data, _keystream(bytes_data.shape, diffusion_key)).astype(np.float64) / 65535.0
    scale = np.asarray(metadata["scale"], dtype=np.float64)
    minimum = np.asarray(metadata["minimum"], dtype=np.float64)
    if coefficients.ndim == 3:
        scale = scale.reshape(1, 1, -1)
        minimum = minimum.reshape(1, 1, -1)
    coefficients = coefficients * scale + minimum
    restored = inverse_arnold_map(_idct2(coefficients), arnold_iterations)
    shape = tuple(metadata["shape"])
    recovered = np.clip(restored[:shape[0], :shape[1]], 0.0, 1.0)
    recovered[np.abs(recovered) < 1e-3] = 0.0
    return recovered


def encryption_steps(image, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Return named intermediate arrays for the step-by-step UI."""
    original = _validate(image)
    scrambled = arnold_map(original, arnold_iterations)
    coefficients = _dct2(scrambled)
    encrypted, metadata = encrypt(original, arnold_iterations, diffusion_key)
    return [("Original", original), ("Arnold cat map", scrambled), ("DCT coefficients", np.log1p(np.abs(coefficients))), ("Diffusion", encrypted)], metadata


def decryption_steps(ciphertext, metadata, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Return named intermediate arrays for the decryption step viewer."""
    encrypted = _validate(ciphertext)
    bytes_data = np.rint(encrypted * 65535.0).astype(np.uint16)
    coefficients = np.bitwise_xor(bytes_data, _keystream(bytes_data.shape, diffusion_key)).astype(np.float64) / 65535.0
    coefficients = coefficients * metadata["scale"] + metadata["minimum"]
    idct = _idct2(coefficients)
    restored = inverse_arnold_map(idct, arnold_iterations)
    return [("Ciphertext", encrypted), ("After diffusion reversal", np.log1p(np.abs(coefficients))), ("IDCT", idct), ("Inverse Arnold map", np.clip(restored, 0.0, 1.0))]


def save_cipher_png(path, ciphertext, metadata):
    """Store an Arnold ciphertext and its reversible scale metadata as PNG."""
    pixels = np.rint(np.clip(ciphertext, 0.0, 1.0) * 65535.0).astype(np.uint16)
    shape = tuple(metadata["shape"])
    encoded = pixels if len(shape) == 2 else pixels.reshape(shape[0], shape[1] * shape[2])
    info = PngImagePlugin.PngInfo()
    info.add_text("arnold_minimum", repr(metadata["minimum"]))
    info.add_text("arnold_scale", repr(metadata["scale"]))
    info.add_text("arnold_shape", ",".join(str(value) for value in shape))
    Image.fromarray(encoded, mode="I;16").save(path, pnginfo=info)


def load_cipher_png(path):
    """Load an Arnold PNG ciphertext and return its ciphertext/metadata pair."""
    image = Image.open(path)
    required = ("arnold_minimum", "arnold_scale", "arnold_shape")
    if not all(key in image.text for key in required):
        raise ValueError("PNG is missing Arnold ciphertext metadata")
    metadata = {"minimum": ast.literal_eval(image.text["arnold_minimum"]), "scale": ast.literal_eval(image.text["arnold_scale"]), "shape": tuple(int(value) for value in image.text["arnold_shape"].split(","))}
    shape = metadata["shape"]
    pixels = np.asarray(image, dtype=np.float64) / 65535.0
    if len(shape) == 3:
        pixels = pixels.reshape(shape)
    return pixels, metadata
