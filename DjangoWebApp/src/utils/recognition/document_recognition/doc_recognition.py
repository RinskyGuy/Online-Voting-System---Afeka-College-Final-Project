import os
import torch
from torch import nn
from efficientnet_pytorch import EfficientNet
import numpy as np
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from django.contrib.staticfiles.storage import staticfiles_storage
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT

IMAGE_SIZE = 200
DEVICE = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

class SiameseNetwork(nn.Module):
    def __init__(self):
        super(SiameseNetwork, self).__init__()
        
        self.base_cnn = EfficientNet.from_pretrained('efficientnet-b3') # 1536
        self.fc = nn.Sequential(nn.Linear(1536 , 512),
                                nn.BatchNorm1d(512),
                                nn.Dropout(0.3),
                                nn.Linear(512 , 256))
    
    def get_vector(self, x):
        x = self.base_cnn.extract_features(x)
        x = self.base_cnn._avg_pooling(x)
        x = x.flatten(start_dim=1)
        x = self.base_cnn._dropout(x)
        x = self.fc(x)
        
        return x

    
class SiameseModel:
    def __init__(self, verbose=False):
        self.model = SiameseNetwork().to(DEVICE)
        
    def compile(self, loss_fn, path=None):
        self.loss_fn = loss_fn
        if path is not None:
            self.load(path)
            
    # load checkpoint from path
    def load(self, path):
        map_location = DEVICE.type if DEVICE.type=='cpu' else None
        self.model.load_state_dict(torch.load(path, map_location=map_location)['model_state_dict'])
        self.model.eval()
    
    def _get_batch(self, image):
        if not isinstance(image, np.ndarray):
            # return RGB ndarray format
            image = np.array(image)
            if image.shape[2] > 3: # RGBA -> RGB
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #cv2.imwrite(r'C:\Users\User\Desktop\Final project\Django website\logs\dec_ver.jpg',image) 
        transforms = self._get_transforms()
        transformed = transforms(image=image)
        image = transformed['image']
        
        if len(image.shape)==2:
            image = image[None, :, :]
        if len(image.shape)==3:
            image = image[None, :, :, :]
        
        assert len(image.shape)==4, f'Expected input data of 4 dimensions, but got {len(image.shape)}.'
        return image
    
    def _get_transforms(self):
        return A.Compose([
            A.Resize(height=IMAGE_SIZE, width=IMAGE_SIZE, p=1),
            A.Normalize(p=1.0),
            ToTensorV2(p=1.0),
        ])
    
    def represent(self, image):
        image = self._get_batch(image)
        vector = self.model.get_vector(image.to(DEVICE).float())
        if len(image)==1:   # single image, return the vector
            return vector[0].cpu()
        return vector.cpu()
    
    def predict(self, doc_scan, docs):
        assert isinstance(docs, dict), f'Expected docs to be a dict mapping document type to document vector, but got {type(docs)}.'
        assert ID in docs, f'"{ID}" missing in {docs}'
        assert DRIVING_LICENSE in docs, f'"{DRIVING_LICENSE}" missing in {docs}'
        assert PASSPORT in docs, f'"{PASSPORT}" missing in {docs}'
        
        min_dist = None
        pred_doc = None
        for doc_type, doc_vector in docs.items():
            if doc_vector is not None:
                dist = self.loss(doc_scan, doc_vector)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    pred_doc = doc_type
        
        print(min_dist)
        #if min_dist > DocRecognition.thresholds[pred_doc]:
        #    return None
        return pred_doc
    
    def loss(self, input_image, true_vector):
        if not torch.is_tensor(true_vector):
            if isinstance(true_vector, list):
                true_vector = np.array(true_vector)
            assert isinstance(true_vector, np.ndarray), f'Expected vector input to be of a list/numpy array/torch tensor, but got {type(doc_vector)}.'
            true_vector = torch.as_tensor(true_vector)
        
        with torch.no_grad():
            input_vector = self.represent(input_image)
            loss = self.loss_fn(input_vector.to(DEVICE), true_vector.to(DEVICE)).detach().item()
        return loss   

doc_siamese_model = SiameseModel()
loss_fn = nn.PairwiseDistance()
model_path = staticfiles_storage.path(os.path.join('models','siamese_model.bin'))
doc_siamese_model.compile(loss_fn, path=model_path)