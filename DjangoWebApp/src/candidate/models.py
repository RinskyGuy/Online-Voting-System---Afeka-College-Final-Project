from django.db import models
import os
import pandas as pd 
from election.models import Election
import shutil

# Create your models here.
class Candidate(models.Model):
    name = models.CharField(max_length=20)
    info = models.CharField(blank=True, max_length=20)
    img_name = models.CharField(blank=True, max_length=20)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id'] 
        
    def __str__(self):
         return self.name
     
    @staticmethod
    def save_from_csv(csv_file):
        if not isinstance(csv_file, pd.core.frame.DataFrame):
            candidates_df = pd.read_csv(csv_file)
        else:
            candidates_df = csv_file
        this_election = Election.objects.all()[0]
        
        for index, row in candidates_df.iterrows():
            candidate = Candidate(name=row['name'], election=this_election)
            if 'file_name' in candidates_df.columns and not pd.isnull(row['file_name']):
                candidate.img_name = row['file_name']
            if 'info' in candidates_df.columns and  not pd.isnull(row['info']):
                candidate.info = row['info']
                
            candidate.save()
    
    @staticmethod
    def get_images_dir():
        return 'static/images/candidates'
        
    @staticmethod      
    def image_validator(img_name):
        img_extension = img_name.split('.')[-1]
        valid_extensions = ['png']
        if not img_extension.lower() in valid_extensions:
            return False
        return True
    

    @staticmethod
    def delete_all_images():
        dir_path = 'static/images/candidates'
        shutil.rmtree(dir_path)
        print("removed images")