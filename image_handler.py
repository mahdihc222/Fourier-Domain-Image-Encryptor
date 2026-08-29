import numpy as np
import matplotlib.pyplot as plt
from imageio.v2 import imread


class ContinuousImage:
    """Represents a grayscale image as a continuous 2D spatial signal. (Given)"""

    def __init__(self, image_path):
        self.image = imread(image_path).astype(float)
        # 3 channels, R, G , B 
        # shape (height,width,3)
        self.image = self.image / np.max(self.image)

        # Continuous spatial coordinate vectors, both spanning [-1, 1]
        self.x = np.linspace(-1, 1, self.image.shape[1])
        self.y = np.linspace(-1, 1, self.image.shape[0])
        print(self.image)

    def showImagePlot(self, title="Image"):
        plt.imshow(self.image)
        plt.title(title)
        plt.axis('off')
        plt.show()

    

