from deepface import DeepFace
from deepface.basemodels import VGGFace
import numpy as np
import cv2
from .face_detector import detector

class DocFaceRec:
    def __init__(self):
        self.model = VGGFace.loadModel()
        self.image_size = 224
     
    def __assert_np_array(self, vector):
        if isinstance(vector, list):
            vector = np.array(vector)
        
        if isinstance(vector, str):
            vector = np.fromstring(vector[1:-1], dtype=np.float, sep=' ')
            
        assert isinstance(vector, np.ndarray), "Vector input should be numpy array."
        return vector
        
        
    def euclidean_distance(self, true_vector, input_vector):
        if true_vector is None or input_vector is None:
            return None
        true_vector = self.__assert_np_array(true_vector)
        input_vector = self.__assert_np_array(input_vector)
        
        distance_vector = np.square(true_vector - input_vector)
        return np.sqrt(distance_vector.sum())
    
    def cosine_distance(self, true_vector, input_vector):
        true_vector = self.__assert_np_array(true_vector)
        input_vector = self.__assert_np_array(input_vector)
        
        a = np.matmul(np.transpose(true_vector), input_vector)
        b = np.matmul(np.transpose(true_vector), true_vector)
        c = np.matmul(np.transpose(input_vector), input_vector)

        return 1 - (a / (np.sqrt(b) * np.sqrt(c)))
    
    def get_vector(self, image): #, detector=None):
        if isinstance(image, str): # assume path was given
            image = cv2.imread(image)
        
        if not isinstance(image, np.ndarray):
            # return RGB ndarray format
            image = np.array(image)
            if image.shape[2] > 3: # RGBA -> RGB
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        face_image = detector.get_face_image(image)
        
        return np.array(DeepFace.represent(img_path=face_image, model = self.model, detector_backend='skip'), np.float)
    
    def get_distance_from_pair(self, img1, img2, detector=None, distance='cosine'):
        vector1 = self.get_vector(face_image=img1, detector=detector)
        vector2 = self.get_vector(face_image=img2, detector=detector)
        
        if distance=='cosine':
            return self.cosine_distance(vector1, vector2)
        elif distance=='euclidean':
            return self.euclidean_distance(vector1, vector2)
    
face_rec_model = DocFaceRec()