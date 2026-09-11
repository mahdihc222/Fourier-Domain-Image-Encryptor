import numpy as np

def generate_phase_mask(shape, seed=None):
    if len(shape) != 2:
        raise ValueError("shape must contain exactly height and width")
    if shape[0] <= 0 or shape[1] <= 0:
        raise ValueError("shape dimensions must be positive")

    rng = np.random.default_rng(seed)
    angles = rng.uniform(0.0, 2.0 * np.pi, size=shape)
    return np.exp(1j * angles)

def encrypt(image, key1, key2):
    image, key1, key2 = _validate_inputs(image, key1, key2)

    # For RGB data, key1[..., None] changes (height, width) into
    # (height, width, 1). That final length-one axis broadcasts over channels.
    broadcast_key1 = key1 if image.ndim == 2 else key1[..., None]
    broadcast_key2 = key2 if image.ndim == 2 else key2[..., None]

    masked_image = image * broadcast_key1
    spectrum = np.fft.fft2(masked_image, axes=(0, 1))

    scrambled_spectrum = spectrum * broadcast_key2
    return np.fft.ifft2(scrambled_spectrum, axes=(0, 1))


def decrypt(ciphertext, key1, key2):
    ciphertext, key1, key2 = _validate_inputs(
        ciphertext, key1, key2, dtype=complex
    )
    broadcast_key1 = key1 if ciphertext.ndim == 2 else key1[..., None]
    broadcast_key2 = key2 if ciphertext.ndim == 2 else key2[..., None]

    spectrum = np.fft.fft2(ciphertext, axes=(0, 1))
    masked_image = np.fft.ifft2(
        spectrum * np.conj(broadcast_key2), axes=(0, 1)
    )
    return (masked_image * np.conj(broadcast_key1)).real


def _validate_inputs(image, key1, key2, dtype=float):
    image = _validate_array(image, dtype)
    key1 = np.asarray(key1, dtype=complex)
    key2 = np.asarray(key2, dtype=complex)

    if key1.shape != image.shape[:2] or key2.shape != image.shape[:2]:
        raise ValueError("both keys must match the image height and width")
    for key in (key1, key2):
        if not np.all(np.isfinite(key)) or not np.allclose(np.abs(key), 1.0):
            raise ValueError("keys must contain finite unit-magnitude phase values")

    return image, key1, key2


def _validate_array(data, dtype=complex):
    data = np.asarray(data, dtype=dtype)
    if data.ndim not in (2, 3) or (data.ndim == 3 and data.shape[2] != 3):
        raise ValueError("data must be a 2-D grayscale or 3-channel RGB array")
    if data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("data must be nonempty and contain only finite values")
    return data


def save_keys(path, key1, key2):
    key1 = np.asarray(key1, dtype=complex)
    key2 = np.asarray(key2, dtype=complex)

    if key1.ndim != 2 or key2.shape != key1.shape:
        raise ValueError("both keys must be 2-D arrays with the same shape")

    np.savez_compressed(path, key1=key1, key2=key2)


def load_keys(path):
    with np.load(path) as saved_file:
        if "key1" not in saved_file or "key2" not in saved_file:
            raise ValueError("key file must contain arrays named key1 and key2")

        key1 = np.asarray(saved_file["key1"], dtype=complex)
        key2 = np.asarray(saved_file["key2"], dtype=complex)

    if key1.ndim != 2 or key2.shape != key1.shape:
        raise ValueError("loaded keys must be 2-D arrays with the same shape")

    return key1, key2

def save_cipher(path, ciphertext):
    ciphertext = _validate_array(ciphertext)

    np.savez_compressed(path, ciphertext=ciphertext, image_shape=ciphertext.shape)


def load_cipher(path):
    saved_file = np.load(path)
    if not isinstance(saved_file, np.lib.npyio.NpzFile):
        raise ValueError("cipher file must be a NumPy .npz archive")
    with saved_file:
        if "ciphertext" not in saved_file:
            raise ValueError("cipher file must contain an array named ciphertext")
        return _validate_array(saved_file["ciphertext"])
