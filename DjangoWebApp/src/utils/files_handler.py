import os
import numpy as np
from PIL import Image, ImageOps

def open_file(image_file):
    image = Image.open(image_file)
    image = ImageOps.exif_transpose(image)
    return image    

def save_image(image, dir_path, image_name):
    if isinstance(image, np.ndarray) or isinstance(image, list):
        image = Image.fromarray(image)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    image_path = os.path.join(dir_path, image_name)
    image.save(image_path)