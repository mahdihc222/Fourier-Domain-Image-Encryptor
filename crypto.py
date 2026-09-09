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


def _validate_inputs(image, key1, key2):
    image = np.asarray(image, dtype=float)
    key1 = np.asarray(key1, dtype=complex)
    key2 = np.asarray(key2, dtype=complex)

    if image.ndim not in (2, 3):
        raise ValueError("image must be a 2-D grayscale or 3-D color array")
    if key1.shape != image.shape[:2] or key2.shape != image.shape[:2]:
        raise ValueError("both keys must match the image height and width")

    return image, key1, key2


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
    ciphertext = np.asarray(ciphertext, dtype=complex)
    if ciphertext.ndim not in (2, 3):
        raise ValueError("ciphertext must be a 2-D grayscale or 3-D color array")

    np.savez_compressed(path, ciphertext=ciphertext, image_shape=ciphertext.shape)


def load_cipher(path):
    with np.load(path) as saved_file:
        ciphertext = np.asarray(saved_file["ciphertext"], dtype=complex)
        return ciphertext