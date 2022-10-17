from tkinter import X
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT

class DocRecognition:
    thresholds = {ID:13.5,
                  DRIVING_LICENSE:12.6,
                  PASSPORT:15.3}
    
class TextVerification:
    thresholds = {ID:0.44,
                  DRIVING_LICENSE:0.56,
                  PASSPORT:0.4}
    
class FaceRecognition:
    thresholds = {ID:13.5,
                  DRIVING_LICENSE:2,
                  PASSPORT:2}