from yoloface import face_analysis
import numpy as np
import cv2            
            
class FaceDetector:
    def __init__(self):
        self.detectos = self.detector = face_analysis() 

    def get_detection(self, image):
        if not isinstance(image, np.ndarray):
            # return BGR ndarray format
            image = np.array(image)
            if image.shape[2] > 3: # RGB -> BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
        detections = self.detector.face_detection(frame_arr=image, frame_status=True, model='tiny')

        bbox = None
        best_score = None

        for i,detection in enumerate(detections[1]):
            score = detections[2][i]
            if best_score is None or score < best_score:
                best_score = score
                bbox = detection
        
        return bbox
        
    def get_face_image(self, image):
        bbox = self.get_detection(image)
        
        if bbox is not None:
            x, y, h, w = bbox
            return image[y:y+h, x:x+w]

detector = FaceDetector()