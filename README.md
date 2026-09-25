# Fourier-Domain Image Encryptor

A desktop application for encrypting and decrypting images using three different frequency-domain and chaotic-map encryption schemes. Built with Python, NumPy, and PySide6 (Qt).

## Goal

This project implements and compares multiple image encryption algorithms that operate in the transform domain rather than the spatial domain. The core idea is to scramble image data using mathematical transforms (Fourier, DCT, DWT) combined with secret keys so that the encrypted image is visually unintelligible and statistically uncorrelated with the original — yet perfectly recoverable with the correct key.

The application serves both as a **practical tool** (encrypt/decrypt real images, save/load ciphertexts and keys as PNG files) and as an **educational demo** (step-by-step visualisation of each stage and side-by-side scheme comparison).

## Encryption Schemes

### 1. Classic DRPE (Double Random Phase Encoding)
- Multiplies the image by a random phase mask **K₁** in the spatial domain.
- Applies a 2-D FFT to move into the Fourier domain.
- Multiplies by a second random phase mask **K₂** in the frequency domain.
- Applies an inverse FFT to produce the complex-valued ciphertext.
- Decryption reverses each step using the conjugate of the keys.

### 2. Arnold + DCT + Diffusion
- Scrambles pixel positions with the **Arnold cat-map** (generalised to non-square images via square tiling).
- Transforms the scrambled image with an orthonormal **2-D DCT**.
- Diffuses the DCT coefficients by XOR-ing with a deterministic keystream derived from a passphrase.
- Decryption reverses diffusion → IDCT → inverse Arnold map.

### 3. DWT + Chaotic Permutation
- Decomposes the image with a **two-level Haar DWT**.
- Packs all seven sub-band coefficient arrays into a single vector.
- Permutes the vector using a **logistic-map** sequence seeded from a master key.
- Decryption inverts the permutation and reconstructs via the inverse DWT.

## Features

- Load any PNG / JPG / BMP / WebP image.
- Encrypt and decrypt with a one-click workflow.
- Save encrypted ciphertexts as lossless 16-bit PNG files (with embedded metadata — no sidecar files needed).
- Save and load DRPE phase keys as PNG.
- **Step-by-step viewer** for both encryption and decryption pipelines.
- **Scheme comparison table** (MSE, PSNR, entropy, correlation, runtime).
- Dark / light theme toggle.

## Requirements

- Python 3.10+
- NumPy
- Pillow (PIL)
- PySide6
- imageio
- matplotlib (used only by `image_handler.py` for optional plotting)

Install all dependencies:

```bash
pip install numpy pillow PySide6 imageio matplotlib
```

## Running

```bash
python main.py
```

## Project Structure

See [`details.md`](details.md) for a full breakdown of every file and function.

```
Image Encryptor/
├── main.py                  # Application entry point
├── crypto.py                # DRPE encrypt / decrypt / key I/O
├── arnold_dct.py            # Arnold + DCT + diffusion scheme
├── dwt_chaotic.py           # DWT + logistic-map scheme
├── image_codec.py           # PNG codec for complex arrays and phase keys
├── image_handler.py         # Image loader (normalises to float64 [0,1])
├── comparison_metrics.py    # MSE, PSNR, entropy, correlation metrics
├── temp_probe.py            # Developer-only DWT debugging script
├── ui/
│   ├── main_window.py       # Main application window
│   ├── key_dialog.py        # Phase-key generation / save / load dialog
│   ├── comparison_dialog.py # Side-by-side scheme metrics table
│   ├── steps_dialog.py      # Step-by-step intermediate image viewer
│   ├── processing_dialog.py # "How it works" DRPE pipeline diagram
│   ├── image_preview.py     # Resizable image preview widget
│   └── styles.py            # Dark and light Qt stylesheets
└── tests/
    ├── test_crypto.py       # DRPE round-trip and validation tests
    └── test_dwt_chaotic.py  # DWT/Haar and permutation tests
```

## License

This project is provided for academic and educational purposes.
