import numpy as np
import matplotlib.pyplot as plt
from imageio.v2 import imread


class ContinuousImage:
    """Represents a grayscale image as a continuous 2D spatial signal. (Given)"""

    def __init__(self, image_path):
        raw_image = imread(image_path)
        if raw_image.ndim == 3 and raw_image.shape[2] == 4:
            raw_image = raw_image[:, :, :3]

        if raw_image.ndim not in (2, 3):
            raise ValueError("image must be grayscale or RGB/RGBA")
        if raw_image.ndim == 3 and raw_image.shape[2] != 3:
            raise ValueError("color image must have three visible channels")

        image = raw_image.astype(np.float64)
        if np.issubdtype(raw_image.dtype, np.integer):
            image /= np.iinfo(raw_image.dtype).max
        self.image = np.clip(image, 0.0, 1.0)

        # Continuous spatial coordinate vectors, both spanning [-1, 1]
        self.x = np.linspace(-1, 1, self.image.shape[1])
        self.y = np.linspace(-1, 1, self.image.shape[0])

    def showImagePlot(self, title="Image"):
        plt.imshow(self.image)
        plt.title(title)
        plt.axis('off')
        plt.show()

    

