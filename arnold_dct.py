"""Arnold-map, DCT, and lightweight diffusion encryption scheme.

The image is scrambled by a reversible Arnold cat map, transformed with an
orthonormal 2-D DCT, diffused with a deterministic XOR keystream, and then
returned through the inverse operations during decryption. The implementation
keeps the original image shape and supports grayscale or RGB arrays.
"""
import hashlib
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
    side = min(image.shape[:2])
    source = image[:side, :side]
    for row in range(side):
        for column in range(side):
            new_row = (row + column) % side
            new_column = (row + 2 * column) % side
            result[new_row, new_column] = source[row, column]
    return result


def arnold_map(image, iterations=1):
    """Apply the Arnold cat map to the largest square image region."""
    result = _validate(image)
    for _ in range(int(iterations) % _arnold_period(result.shape[0], result.shape[1])):
        result = _arnold_once(result)
    return result


def inverse_arnold_map(image, iterations=1):
    """Reverse :func:`arnold_map` using the inverse coordinate mapping."""
    result = _validate(image)
    side = min(result.shape[:2])
    for _ in range(int(iterations) % _arnold_period(result.shape[0], result.shape[1])):
        restored = result.copy()
        for row in range(side):
            for column in range(side):
                old_row = (2 * row - column) % side
                old_column = (-row + column) % side
                restored[old_row, old_column] = result[row, column]
        result = restored
    return result


def _arnold_period(height, width):
    side = min(height, width)
    probe = np.arange(side * side).reshape(side, side)
    current = probe.copy()
    for period in range(1, side * side * 2 + 1):
        current = _arnold_once(current)
        if np.array_equal(current, probe):
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
    return np.random.default_rng(seed_value).integers(0, 256, size=shape, dtype=np.uint8)


def encrypt(image, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Run Arnold -> DCT -> diffusion and return a float image ciphertext."""
    original = _validate(image)
    scrambled = arnold_map(original, arnold_iterations)
    coefficients = _dct2(scrambled)
    minimum, maximum = float(coefficients.min()), float(coefficients.max())
    scale = maximum - minimum or 1.0
    normalized = np.rint(np.clip((coefficients - minimum) / scale, 0.0, 1.0) * 255).astype(np.uint8)
    diffused = np.bitwise_xor(normalized, _keystream(normalized.shape, diffusion_key))
    return diffused.astype(np.float64) / 255.0, {"minimum": minimum, "scale": scale, "shape": original.shape}


def decrypt(ciphertext, metadata, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Reverse diffusion -> IDCT -> inverse Arnold using encryption metadata."""
    encrypted = _validate(ciphertext)
    bytes_data = np.rint(encrypted * 255.0).astype(np.uint8)
    coefficients = np.bitwise_xor(bytes_data, _keystream(bytes_data.shape, diffusion_key)).astype(np.float64) / 255.0
    coefficients = coefficients * metadata["scale"] + metadata["minimum"]
    restored = inverse_arnold_map(_idct2(coefficients), arnold_iterations)
    shape = tuple(metadata["shape"])
    return np.clip(restored[:shape[0], :shape[1]], 0.0, 1.0)


def encryption_steps(image, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Return named intermediate arrays for the step-by-step UI."""
    original = _validate(image)
    scrambled = arnold_map(original, arnold_iterations)
    coefficients = _dct2(scrambled)
    encrypted, metadata = encrypt(original, arnold_iterations, diffusion_key)
    return [("Original", original), ("Arnold cat map", scrambled), ("DCT coefficients", np.abs(coefficients)), ("Diffusion", encrypted)], metadata


def decryption_steps(ciphertext, metadata, arnold_iterations=3, diffusion_key="image-encryptor"):
    """Return named intermediate arrays for the decryption step viewer."""
    encrypted = _validate(ciphertext)
    bytes_data = np.rint(encrypted * 255.0).astype(np.uint8)
    coefficients = np.bitwise_xor(bytes_data, _keystream(bytes_data.shape, diffusion_key)).astype(np.float64) / 255.0
    coefficients = coefficients * metadata["scale"] + metadata["minimum"]
    idct = _idct2(coefficients)
    restored = inverse_arnold_map(idct, arnold_iterations)
    return [("Ciphertext", encrypted), ("After diffusion reversal", coefficients), ("IDCT", idct), ("Inverse Arnold map", np.clip(restored, 0.0, 1.0))]


def save_cipher_png(path, ciphertext, metadata):
    """Store an Arnold ciphertext and its reversible scale metadata as PNG."""
    pixels = np.rint(np.clip(ciphertext, 0.0, 1.0) * 255.0).astype(np.uint8)
    info = PngImagePlugin.PngInfo()
    info.add_text("arnold_minimum", repr(metadata["minimum"]))
    info.add_text("arnold_scale", repr(metadata["scale"]))
    info.add_text("arnold_shape", ",".join(str(value) for value in metadata["shape"]))
    Image.fromarray(pixels if pixels.ndim == 2 else pixels, mode="L" if pixels.ndim == 2 else "RGB").save(path, pnginfo=info)


def load_cipher_png(path):
    """Load an Arnold PNG ciphertext and return its ciphertext/metadata pair."""
    image = Image.open(path)
    required = ("arnold_minimum", "arnold_scale", "arnold_shape")
    if not all(key in image.text for key in required):
        raise ValueError("PNG is missing Arnold ciphertext metadata")
    pixels = np.asarray(image.convert("RGB" if image.mode == "RGB" else "L"), dtype=np.float64) / 255.0
    metadata = {"minimum": float(image.text["arnold_minimum"]), "scale": float(image.text["arnold_scale"]), "shape": tuple(int(value) for value in image.text["arnold_shape"].split(","))}
    return pixels, metadata
