from .models import Election
from voter.models import Voter
from candidate.models import Candidate
from datetime import datetime,timedelta
from django.contrib.staticfiles.storage import staticfiles_storage
from utils.files_handler import save_image
from PIL import Image
from django.contrib.staticfiles.storage import staticfiles_storage
from utils.documents import ID, DRIVING_LICENSE, PASSPORT
import pandas as pd
import os
import cv2

def create_elections(start_date, end_date):
    start_date = datetime.now() + timedelta(days=1)
    end_date = datetime.now() + timedelta(days=2)
    
    Election.objects.get_or_create(start_time=datetime.combine(start_date.date(),start_date.time()), 
                                            end_time=datetime.combine(end_date.date(),end_date.time()))
    
def create_voters():
    voters_data = pd.read_pickle(staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'voters_data.csv')))
   
    paths = {ID: staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'ids')), 
             DRIVING_LICENSE: staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'driving_licenses')), 
             PASSPORT: staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'passports'))}
    
    for index, person in voters_data.iterrows():
        images = {ID: None, DRIVING_LICENSE: None, PASSPORT: None}
        
        for doc_type, path in paths.items():
            for img in os.listdir(path):
                if person['id_num'] in img:
                    images[doc_type] = cv2.imread(os.path.join(path, img))
       
        Voter.objects.get_or_create(person, images[ID], images[DRIVING_LICENSE], images[PASSPORT])

def create_candidates():
    path = staticfiles_storage.path(os.path.join(os.path.join('tests', 'candidates')))
    candidates_data = pd.read_csv(os.path.join(path, 'candidates.csv'))
   
    Candidate.save_from_csv(candidates_data)
    
    for index, candidate in candidates_data.iterrows():
        image_name = candidate['file_name']
        if image_name in os.listdir(path):
            save_image(Image.open(os.path.join(path, image_name)), Candidate.get_images_dir(), candidate['file_name'])
            

def initialize_elections():
    elections = Election.objects.all()
    if len(elections) == 0:
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=2)
        
        create_elections(start_date, end_date)
        create_candidates()
        create_voters()
        
