from matplotlib import pyplot as plt
import numpy as np
import wandb
import cv2
import os

class DebugToWandb:
    _ID = 0
    _run = None
    _run_dir = ''
    
    def __init__(self, doc_type):
        self.id = self._ID 
        self.__class__._ID += 1
        self.__initialize_run(doc_type)
        
    def debug_multiple_imgs(self, imgs, titles):
        assert isinstance(imgs, list), f'Expected a list of image as input, but got {str(type(imgs))}.'
        assert len(imgs) == len(titles), f'Expected number of images ({len(imgs)}) to be equal to number of titles ({len(titles)}).'
        
        for img, title in zip(imgs,titles):
            assert isinstance(img, np.ndarray), f'Expected item in list to be numpy array representation of image, but got {str(type(img))}.'
            self.debug_single_img(img, title)
                
    def debug_single_img(self, img, title):
        self._run.log({f'{self._run_dir}/{self.id}/{title}': wandb.Image(img)})
        
    def __initialize_run(self, doc_type):
        if self._run is None:
            wandb.login(key="20bdd9444c6ee7c1b08f9c310d1943be6614c45c")
            self.__class__._run = wandb.init(project="final-project", name="doc_OCR", mode='online')
            self._run_dir = doc_type + '/doc_image_processing'

class DebugToPlt:
    def debug_multiple_imgs(self, imgs, titles):
        assert isinstance(imgs, list), f'Expected a list of image as input, but got {str(type(imgs))}.'
        assert len(imgs) == len(titles), f'Expected number of images ({len(imgs)}) to be equal to number of titles ({len(titles)}).'
        
        plt.figure(figsize=(30, 20))
        num_imgs = len(imgs)

        for i, (img, title) in enumerate(zip(imgs, titles)):
            assert isinstance(img, np.ndarray), f'Expected item in list to be numpy array representation of image, but got {str(type(img))}.'

            plt.subplot(1, 4, i+1)
            plt.imshow(img, cmap="gray")
            plt.title(title)
                
    def debug_single_img(self, img, title=None):
        plt.figure(figsize=(10, 5))
        plt.imshow(img, cmap="gray")
        plt.title(title)

class DebugToFile:
    def __init__(self, debug_dir):
        self.debug_dir = debug_dir
        if not os.path.exists(debug_dir):
            os.makedirs(self.debug_dir)
                
    def debug_multiple_imgs(self, imgs, titles):
        assert isinstance(imgs, list), f'Expected a list of image as input, but got {str(type(imgs))}.'
        assert len(imgs) == len(titles), f'Expected number of images ({len(imgs)}) to be equal to number of titles ({len(titles)}).'

        for img, title in zip(imgs, titles):
            assert isinstance(img, np.ndarray), f'Expected item in list to be numpy array representation of image, but got {str(type(img))}.'  
            self.debug_single_img(img, title)

                
    def debug_single_img(self, img, title):
        cv2.imwrite(os.path.join(self.debug_dir, title+'.jpg'), img)
        

