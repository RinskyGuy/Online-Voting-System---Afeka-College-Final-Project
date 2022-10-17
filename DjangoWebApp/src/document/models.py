#from abc import abstractstaticmethod
from django.db import models
from .validators import LicenseValidators, PassPortValidators
from utils.recognition.document_recognition.regex import DateValidator, StringValidator, NameValidator
from utils.recognition.document_recognition.doc_recognition import doc_siamese_model
from utils.recognition.face_recognition.face_recognition import face_rec_model
from utils.recognition.document_recognition.documents import IdData, DrivingLicenseData, PassportData
from django.forms.models import model_to_dict
import ast

class Document(models.Model):
    id_num = models.CharField(primary_key=True, max_length=10, verbose_name="ID", validators=[StringValidator.validate_id_num]) 
    birth_date = models.DateField(verbose_name="Birth date")
    gen_date = models.DateField()
    exp_date = models.DateField()
    face_vector = models.TextField()
    doc_vector = models.TextField()
    
    class Meta:
        abstract = True
    
    def _get_doc_vector(image):
        doc_vector = doc_siamese_model.represent(image)
        return str(doc_vector.tolist())
    
    def _get_face_vector(image):    
        face_vector = face_rec_model.get_vector(image)
        return str(face_vector.tolist())
    
class IdQuerySet(models.query.QuerySet):
    def get_or_create(self, data, image):
        docs_from_db = IdDocument.objects.filter(id_num=data['id_num'])
        if len(docs_from_db)!=0:
            return False, docs_from_db[0]
        
        else:
            id_doc = IdDocument.initialize(data, image)
            id_doc.save()
            print('id created!')
            return True, id_doc
        
class IdManager(models.Manager):
    def get_queryset(self):
        return IdQuerySet(self.model)
    
class IdDocument(Document):
    heb_first_name = models.CharField(max_length=20, verbose_name="First name (hebrew)", validators=[NameValidator.validate_heb_name])
    heb_last_name = models.CharField(max_length=20, verbose_name="Last name (hebrew)", validators=[NameValidator.validate_heb_name])
    
    objects = IdManager()
    
    def initialize(data, image):    
        gen_date = DateValidator.str_to_date(data['gen_date'])
        exp_date = DateValidator.str_to_date(data['exp_date'])
        birth_date = DateValidator.str_to_date(data['birth_date'])
        
        doc = IdDocument(id_num = data['id_num'],
                         heb_first_name = data['heb_first_name'],
                         heb_last_name = data['heb_last_name'],
                         gen_date = gen_date, 
                         exp_date = exp_date, 
                         birth_date = birth_date,
                         face_vector = Document._get_face_vector(image),
                         doc_vector = Document._get_doc_vector(image))
        return doc

    def get_dict(self, field=None):
        data = {}
        doc_data = model_to_dict(self)
        
        for key,value in doc_data.items():
            if key in IdData.labels:
                if key.endswith('date'):
                    data[key] = value.strftime('%d.%m.%Y')
                    data['heb_'+key] = DateValidator.get_heb_date(value)
                else:
                    data[key] = value 
                    
            elif key.endswith('vector'):
                data[key] = ast.literal_eval(value)

        if field == None:
            return data
        
        assert field in data, f'{field} not found for this document.'        
        return data[field]
    
class DrivingLicenseQuerySet(models.query.QuerySet):
    def get_or_create(self, data, image):
        docs_from_db = DrivingLicenseDocument.objects.filter(id_num=data['id_num'])
        if len(docs_from_db)!=0:
            return False, docs_from_db[0]
        
        else:
            driving_license_doc = DrivingLicenseDocument.initialize(data, image)
            driving_license_doc.save()
            print('driving license created!')
            return True, driving_license_doc
        
class DrivingLicenseManager(models.Manager):
    def get_queryset(self):
        return DrivingLicenseQuerySet(self.model)        
    
class DrivingLicenseDocument(Document):
    first_name = models.CharField(max_length=20, validators=[NameValidator.validate_eng_name])
    last_name = models.CharField(max_length=20, validators=[NameValidator.validate_eng_name])
    heb_first_name = models.CharField(max_length=20, validators=[NameValidator.validate_heb_name])
    heb_last_name = models.CharField(max_length=20, validators=[NameValidator.validate_heb_name])
    address = models.CharField(max_length=50)
    license_num = models.CharField(max_length=8)
    unique_num = models.CharField(max_length=4, validators=[LicenseValidators.unique_num_validator])
    
    objects = DrivingLicenseManager()
    
    def initialize(data, image):
        gen_date = DateValidator.str_to_date(data['gen_date'])
        exp_date = DateValidator.str_to_date(data['exp_date'])
        birth_date = DateValidator.str_to_date(data['birth_date'])
        
        doc = DrivingLicenseDocument(id_num = data['id_num'],
                                     first_name = data['first_name'],
                                     last_name = data['last_name'],
                                     heb_first_name = data['heb_first_name'],
                                     heb_last_name = data['heb_last_name'],
                                     gen_date = gen_date, 
                                     exp_date = exp_date, 
                                     birth_date = birth_date,
                                     address = data['address'],
                                     license_num = data['license_num'],
                                     unique_num = data['unique_num'],
                                     face_vector = Document._get_face_vector(image),
                                     doc_vector = Document._get_doc_vector(image))
        return doc

    def get_dict(self, field=None):
        data = {}
        doc_data = model_to_dict(self)
        
        for key,value in doc_data.items():
            if key in DrivingLicenseData.labels:
                if key.endswith('date'):
                    data[key] = value.strftime('%d.%m.%Y')
                else:
                    data[key] = value 
                    
            elif key.endswith('vector'):
                data[key] = ast.literal_eval(value)

        if field == None:
            return data
        
        assert field in data, f'{field} not found for this document.'        
        return data[field]

class PassportQuerySet(models.query.QuerySet):
    def get_or_create(self, data, image):
        docs_from_db = PassportDocument.objects.filter(id_num=data['id_num'])
        if len(docs_from_db)!=0:
            return False, docs_from_db[0]
        
        else:
            passport_doc = PassportDocument.initialize(data, image)
            passport_doc.save()
            print('passport created!')
            return True, passport_doc
        
class PassportManager(models.Manager):
    def get_queryset(self):
        return PassportQuerySet(self.model)
    
class PassportDocument(Document):
    first_name = models.CharField(max_length=20, validators=[NameValidator.validate_eng_name])
    last_name = models.CharField(max_length=20, validators=[NameValidator.validate_eng_name])
    passport_num = models.CharField(max_length=8)
    gender = models.CharField(max_length=1, validators=[PassPortValidators.gender_validator])
    
    objects = PassportManager()
    
    def initialize(data, image):     
        gen_date = DateValidator.str_to_date(data['gen_date'])
        exp_date = DateValidator.str_to_date(data['exp_date'])
        birth_date = DateValidator.str_to_date(data['birth_date'])
        
        doc = PassportDocument(id_num = data['id_num'],
                                     first_name = data['first_name'],
                                     last_name = data['last_name'],
                                     gen_date = gen_date, 
                                     exp_date = exp_date, 
                                     birth_date = birth_date,
                                     passport_num = data['passport_num'],
                                     gender = data['gender'],
                                     face_vector = Document._get_face_vector(image),
                                     doc_vector = Document._get_doc_vector(image))
        return doc
    
    def get_dict(self, field=None):
        data = {}
        doc_data = model_to_dict(self)
        
        for key,value in doc_data.items():
            if key in PassportData.labels:
                if key.endswith('date'):
                    data[key] = value.strftime('%d.%m.%Y')
                else:
                    data[key] = value 
                    
            elif key.endswith('vector'):
                data[key] = ast.literal_eval(value)

        if field == None:
            return data
        
        assert field in data, f'{field} not found for this document.'        
        return data[field]