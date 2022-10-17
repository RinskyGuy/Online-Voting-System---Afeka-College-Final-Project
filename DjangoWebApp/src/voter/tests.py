from django.test import RequestFactory, TestCase
from .models import Voter
from django.contrib.auth.models import User
from document.models import IdDocument, DrivingLicenseDocument, PassportDocument
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT
from utils.doc_generator import IdGenerator, DrivingLicenseGenerator, PassportGenerator, DrawDoc
from election.tests import initialize_elections
from django.contrib.staticfiles.storage import staticfiles_storage
import os
import pandas as pd
import numpy as np
from vote.models import Vote
import hashlib

# Get data from file
def get_voters(size=None):
    voters_data = pd.read_pickle(staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'voters_data.csv')))
    
    if size is None:
        return voters_data
    
    return voters_data[:size]

def get_voter_data():
    return get_voters(1).to_dict(orient='records')[0]

def generate_data():
    path = staticfiles_storage.path(os.path.join(os.path.join('tests', 'voter'), 'face_images'))
    images = [None, None, None]
    
    for i, image in enumerate(os.listdir(path)):
        images[i] = os.path.join(path, image)
    
    genrators = {ID:IdGenerator, DRIVING_LICENSE:DrivingLicenseGenerator, PASSPORT:PassportGenerator}
    generated_data = {ID:None, DRIVING_LICENSE:None, PASSPORT:None}
    generated_image = {ID:None, DRIVING_LICENSE:None, PASSPORT:None}
    
    for i, (doc_type, generator) in enumerate(genrators.items()):
        data_generator = generator(images[i], gender='F')
        if doc_type == ID:
            doc_image = DrawDoc(doc_type).gen_doc(data_generator)
        else:
            doc_image = DrawDoc(doc_type).gen_doc(data_generator.generate_data(generated_data['id']))
        doc_data = data_generator.get_data()
        generated_data[doc_type] = doc_data
        
        doc_image = np.array(doc_image)
        generated_image[doc_type] = doc_image
    
    generated_data['id_num'] = generated_data[ID]['id_num']
    return generated_data, generated_image
 
# get data from db
def get_voter():
    #voters = Voter.objects.all()
    #for voter in voters:
    #    yield voter
    return Voter.objects.all()[0]

# test cases
class VoterTestCase(TestCase):
    def setUp(self):
        initialize_elections()
    
    ## Creation test cases ##
    def test_vote_created(self):
        # Give valid voter data
        generated_data, generated_image = generate_data()
        
        # When voter created
        voter = Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])
        
        # Then vote is created
        hashed_unique_num = hashlib.sha256(voter.unique_num.encode()).hexdigest() # in vote
        vote = Vote.objects.filter(unique_num=hashed_unique_num)
        
        self.assertNotEqual(len(vote), 0)
    
    def test_create_voter_with_null_id_data(self):
        # Given voter with null id data
        generated_data, generated_image = generate_data()
        generated_data[ID] = None

        # When voter create - Then raises ValueError (ID data can't be empty)
        with self.assertRaises(ValueError):
            Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])
            
    def test_create_voter_with_null_driving_license_data(self):
        # Given voter with null driving license data
        generated_data, generated_image = generate_data()
        generated_data[DRIVING_LICENSE] = None

        # When voter created
        voter = Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])
        
        # Then driving_license_doc of voter is null
        self.assertEqual(voter.driving_license_doc, None)
        
    def test_create_voter_with_null_passport_data(self):
        # Given voter with null passport data
        generated_data, generated_image = generate_data()
        generated_data[PASSPORT] = None

        # When voter created
        voter = Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])
        
        # Then passport_doc of voter is null
        self.assertEqual(voter.passport_doc, None)
    
    #def test_create_voter_with_existing_id(self):
        # Given voter with existing ID number
     #   voter = get_voter()
      #  id_num = voter.id_doc.id_num
       # generated_data, generated_image = generate_data()
        #generated_data['id_num'] = id_num
        #generated_data[ID]['id_num'] = id_num
        #generated_data[DRIVING_LICENSE]['id_num'] = id_num
        #generated_data[PASSPORT]['id_num'] = id_num
             
        # When voter create - Then raises ValueError (ID number must match document)
        #with self.assertRaises(ValueError):
        #    print(generated_data)
        #    Voter.objects.get_or_create(generated_data, generated_image[ID], generated_image[DRIVING_LICENSE], generated_image[PASSPORT])
            
    def test_crete_voter_with_different_id_in_id_doc(self):
        # Given voter with existing different ID number in ID document
        generated_data1, generated_image1 = generate_data()
        generated_data2, generated_image2 = generate_data()
        generated_data1[ID]['id_num'] = generated_data2[ID]['id_num']
        
        # When voter create - Then raises ValueError (ID number must match document)
        with self.assertRaises(ValueError):
            Voter.objects.get_or_create(generated_data1, generated_image1[ID], generated_image1[DRIVING_LICENSE], generated_image1[PASSPORT])
            
    def test_crete_voter_with_different_id_in_driving_license_doc(self):
        # Given voter with existing different ID number in ID document
        generated_data1, generated_image1 = generate_data()
        generated_data2, generated_image2 = generate_data()
        generated_data1[DRIVING_LICENSE]['id_num'] = generated_data2[DRIVING_LICENSE]['id_num']
        
        # When voter create - Then raises ValueError (ID number must match document)
        with self.assertRaises(ValueError):
            Voter.objects.get_or_create(generated_data1, generated_image1[ID], generated_image1[DRIVING_LICENSE], generated_image1[PASSPORT])
            
    def test_crete_voter_with_different_id_in_passport_doc(self):
        # Given voter with existing different ID number in ID document
        generated_data1, generated_image1 = generate_data()
        generated_data2, generated_image2 = generate_data()
        generated_data1[PASSPORT]['id_num'] = generated_data2[PASSPORT]['id_num']
        
        # When voter create - Then raises ValueError (ID number must match document)
        with self.assertRaises(ValueError):
            Voter.objects.get_or_create(generated_data1, generated_image1[ID], generated_image1[DRIVING_LICENSE], generated_image1[PASSPORT])
            
            
    ## Deletion test cases ## 
    def test_id_delete_on_voter_delete(self):
        # Given a voter from db
        voter = get_voter()
        id = voter.id_doc
        id_num = id.id_num
        
        # When voter is deleted
        voter.delete()
        
        # Then id is deleted
        ids = IdDocument.objects.filter(id_num=id_num)
        self.assertEqual(len(ids), 0)
        
    def test_driving_license_delete_on_voter_delete(self):
        # Given a voter from db
        voter = get_voter()
        driving_license = voter.driving_license_doc
        id_num = driving_license.id_num
        
        # When voter is deleted
        voter.delete()
        
        # Then driving_license is deleted
        driving_licenses = DrivingLicenseDocument.objects.filter(id_num=id_num)
        self.assertEqual(len(driving_licenses), 0)
        
    def test_passport_delete_on_voter_delete(self):
        # Given a voter from db
        voter = get_voter()
        passport = voter.passport_doc
        id_num = passport.id_num
        
        # When voter is deleted
        voter.delete()
        
        # Then passport is deleted
        passports = PassportDocument.objects.filter(id_num=id_num)
        self.assertEqual(len(passports), 0)
        
    def test_vote_delete_on_voter_delete(self):
        # Given a voter from db
        voter = get_voter()
        unique_num = voter.unique_num
        
        # When voter is deleted
        voter.delete()
        
        # Then vote is deleted
        hashed_unique_num = hashlib.sha256(unique_num.encode()).hexdigest() # in vote
        vote = Vote.objects.filter(unique_num=hashed_unique_num)
        
        self.assertEqual(len(vote), 0)

def get_admin():
    admins = User.objects.all()
    if len(admins) == 0:
        path = staticfiles_storage.path(os.path.join(os.path.join('tests', 'admin')))
        admin_data = pd.read_csv(os.path.join(path, 'admin_data.csv'))
        admin = User.objects.create_superuser(admin_data['user'], admin_data['email'], admin_data['password'])
    else:
        admin = admins[0]
    
    return admin
             
# Create your tests here.
class SimpleTest(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        initialize_elections()
        #self.user = User.objects.create_user(
        #    username='jacob', email='jacob@…', password='top_secret')

    def test_details(self):
        # Given user not logged in as admin and election exists
        # When requesting get home page
        request = self.factory.get('/')
        #self.assertTrue(request.user.is_anonymous)
        
        print(request)    
        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        #request.user = self.user

        # Or you can simulate an anonymous user by setting request.user to
        # an AnonymousUser instance.
        #request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /customer/details
        #response = my_view(request)
        # Use this syntax for class-based views.
        #response = MyView.as_view()(request)
        #self.assertEqual(response.status_code, 200)
        
        #response = self.client.get(reverse('create_employee_profile'))
        #self.assertIsInstance(response.context['name_form'], EmployeeNameForm)
    
