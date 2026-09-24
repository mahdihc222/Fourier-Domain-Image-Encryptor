"""Metrics used by the comparison window."""
import numpy as np


def _real(value):
    value = np.asarray(value)
    return np.abs(value) if np.iscomplexobj(value) else value.astype(float)


def entropy(image):
    """Return Shannon entropy in bits per pixel after 8-bit quantization."""
    pixels = np.rint(np.clip(_real(image), 0.0, 1.0) * 255).astype(np.uint8)
    probabilities = np.bincount(pixels.ravel(), minlength=256).astype(float)
    probabilities /= probabilities.sum()
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities)))


def summarize(original, encrypted, decrypted, runtime):
    """Calculate MSE, PSNR, entropy, correlation, and runtime for one scheme."""
    source, recovered = _real(original), np.clip(_real(decrypted), 0.0, 1.0)
    error = float(np.mean((source - recovered) ** 2))
    psnr = float("inf") if error == 0 else float(10 * np.log10(1.0 / error))
    source_flat, encrypted_flat = source.ravel(), _real(encrypted).ravel()
    correlation = 0.0 if np.std(encrypted_flat) == 0 else float(np.corrcoef(source_flat, encrypted_flat)[0, 1])
    return {"MSE": error, "PSNR (dB)": psnr, "Entropy (bits/pixel)": entropy(encrypted), "Correlation": correlation, "Runtime (ms)": runtime * 1000}
