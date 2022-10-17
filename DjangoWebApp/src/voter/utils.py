from django.shortcuts import render
from django.contrib.staticfiles.storage import staticfiles_storage
from utils.doc_generator import IdGenerator, DrivingLicenseGenerator, PassportGenerator, DrawDoc
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT
from .models import Voter
from vote.models import Vote
from utils.files_handler import open_file
from PIL import Image
import hashlib
#from document.models import IdDocument, DrivingLicenseDocument, PassportDocument
#import ast
import os

def get_rand_images(images):
    doc_images = {ID:None, DRIVING_LICENSE:None, PASSPORT:None}
    for image, doc_type in zip(images, list(doc_images.keys())):
        doc_images[doc_type] = image
    
    return doc_images
    
def generate_docs(images, is_uploaded_file='True'):
    genrators = {ID:IdGenerator, DRIVING_LICENSE:DrivingLicenseGenerator, PASSPORT:PassportGenerator}
    
    generated_data = {ID:None, DRIVING_LICENSE:None, PASSPORT:None,}
    generated_image = {ID:None, DRIVING_LICENSE:None, PASSPORT:None,}
    
    images = get_rand_images(images)
    for doc_type, image in images.items():
        if image is not None:
            if is_uploaded_file:
                image = open_file(image)
            elif isinstance(image, str):
                image = Image.open(image)
            data_generator = genrators[doc_type](image)
            if doc_type == ID:
                doc_image = DrawDoc(doc_type).gen_doc(data_generator)
            else:
                doc_image = DrawDoc(doc_type).gen_doc(data_generator.generate_data(generated_data['id']))
            doc_data = data_generator.get_data()
            generated_data[doc_type] = doc_data
            generated_image[doc_type] = doc_image
        
    generated_data['id_num'] = generated_data[ID]['id_num']
    Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])

    #return generated_data
    
def log_to_file(msg, path):
    path = staticfiles_storage.path(path)
    print(path)
    if os.path.exists(path):       
        with open(path, "a") as file_object:
            file_object.write(msg)
            
def get_vectors(docs, field):           
    vectors = {ID:None, DRIVING_LICENSE:None, PASSPORT:None}
    for doc_type, doc_obj in docs.items():
        print(doc_type, doc_obj)
        if doc_obj is not None:
            vectors[doc_type] = doc_obj.get_dict(field)
    
    #print(vectors)
    
    return vectors

def case_admin(request, *args, **kwargs):
    if not request.user.is_anonymous:
        return render(request, "logout.html", {})
    
def get_voter(request, *args, **kwargs):
    if 'voter_unique_code' in request.session.keys():
        voter = Voter.get(request.session['voter_unique_code']) ####3CHANGEEEEEEEEEEEe
        return voter

def get_vote(request, *args, **kwargs):
    if 'voter_unique_code' in request.session.keys():
        unique_num = request.session['voter_unique_code']
        vote = Vote.get(hashlib.sha256(unique_num.encode()).hexdigest()) 
        return vote
    
def check_key_in_session(request, key, *args, **kwargs):
    return key in request.session.keys()