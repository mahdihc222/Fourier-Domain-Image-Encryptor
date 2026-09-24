"""PNG codec for complex ciphertexts and paired phase keys.

Complex values are stored as amplitude and phase in a single RGBA PNG.
Each value uses two 8-bit channels, giving 16-bit quantization for both
components. The amplitude scale and original array shape are stored in PNG
text metadata, so no NumPy archive or sidecar file is required.
"""
import numpy as np
from PIL import Image, PngImagePlugin

_PHASE_LOW = -np.pi
_PHASE_HIGH = np.pi
_SCALE_KEY = "image_encryptor_amplitude_scale"
_SHAPE_KEY = "image_encryptor_shape"
_KEY_WIDTH_KEY = "image_encryptor_key_width"


def _split(values):
    return (values >> 8).astype(np.uint8), (values & 255).astype(np.uint8)


def _join(high, low):
    return (high.astype(np.uint16) << 8) | low.astype(np.uint16)


def _quantize(values, low, high):
    normalized = np.clip((values - low) / (high - low), 0.0, 1.0)
    return np.rint(normalized * 65535.0).astype(np.uint16)


def _dequantize(values, low, high):
    return values.astype(np.float64) / 65535.0 * (high - low) + low


def save_complex_png(path, values):
    """Encode a 2-D or 3-D complex array as one metadata-bearing RGBA PNG."""
    values = np.asarray(values, dtype=complex)
    if values.ndim not in (2, 3) or (values.ndim == 3 and values.shape[2] != 3):
        raise ValueError("values must be grayscale or 3-channel complex data")
    shape = values.shape
    channels = 1 if values.ndim == 2 else values.shape[2]
    flat = values if channels == 1 else values.reshape(values.shape[0], -1)
    scale = float(np.max(np.abs(flat))) or 1.0
    amplitude = _quantize(np.abs(flat), 0.0, scale)
    phase = _quantize(np.angle(flat), _PHASE_LOW, _PHASE_HIGH)
    amp_high, amp_low = _split(amplitude)
    phase_high, phase_low = _split(phase)
    rgba = np.stack((amp_high, amp_low, phase_high, phase_low), axis=-1)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text(_SCALE_KEY, repr(scale))
    metadata.add_text(_SHAPE_KEY, ",".join(str(value) for value in shape))
    Image.fromarray(rgba, mode="RGBA").save(path, pnginfo=metadata)


def load_complex_png(path):
    """Decode a complex array written by :func:`save_complex_png`."""
    image = Image.open(path)
    if _SCALE_KEY not in image.text or _SHAPE_KEY not in image.text:
        raise ValueError("PNG is missing encrypted-image metadata")
    rgba = np.asarray(image.convert("RGBA"))
    amplitude = _dequantize(_join(rgba[..., 0], rgba[..., 1]), 0.0, float(image.text[_SCALE_KEY]))
    phase = _dequantize(_join(rgba[..., 2], rgba[..., 3]), _PHASE_LOW, _PHASE_HIGH)
    return (amplitude * np.exp(1j * phase)).reshape(
        tuple(int(value) for value in image.text[_SHAPE_KEY].split(","))
    )


def save_keypair_png(path, key1, key2):
    """Store two phase masks side by side in one 16-bit-equivalent LA PNG."""
    key1, key2 = np.asarray(key1, complex), np.asarray(key2, complex)
    if key1.ndim != 2 or key2.shape != key1.shape:
        raise ValueError("both keys must be 2-D arrays with the same shape")
    if not all(np.allclose(np.abs(key), 1.0) for key in (key1, key2)):
        raise ValueError("keys must contain unit-magnitude phase values")
    combined = np.concatenate((np.angle(key1), np.angle(key2)), axis=1)
    high, low = _split(_quantize(combined, _PHASE_LOW, _PHASE_HIGH))
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text(_KEY_WIDTH_KEY, str(key1.shape[1]))
    Image.fromarray(np.stack((high, low), axis=-1), mode="LA").save(path, pnginfo=metadata)


def load_keypair_png(path):
    """Decode the two phase masks stored by :func:`save_keypair_png`."""
    image = Image.open(path)
    if _KEY_WIDTH_KEY not in image.text:
        raise ValueError("PNG is missing phase-key metadata")
    width = int(image.text[_KEY_WIDTH_KEY])
    data = np.asarray(image.convert("LA"))
    phase = _dequantize(_join(data[..., 0], data[..., 1]), _PHASE_LOW, _PHASE_HIGH)
    return np.exp(1j * phase[:, :width]), np.exp(1j * phase[:, width:])
