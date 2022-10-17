from django import forms 
from django.forms import ModelForm
from utils.recognition.document_recognition.regex import DateValidator, StringValidator, NameValidator
from .validators import LicenseValidators
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .models import IdDocument
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT

class DocumentBaseForm(forms.Form):
    def get_doc_data(self):
        doc_data = {}
        for field, value in self.cleaned_data.items():
            if field.startswith(self.name+'_'):
                field = '_'.join(field.split('_')[1:])
            doc_data[field] = value
        
        return doc_data
    
    def clean_date(self, gen_date, exp_date):
        err_msgs = []
        invalid = False
        if not DateValidator.is_before(datetime(gen_date.year, gen_date.month, gen_date.day), 
                                                datetime(exp_date.year, exp_date.month, exp_date.day)):
            err_msgs.append("Issue date can't be before expiration date.")
            invalid = True
            
        if not DateValidator.is_before(datetime(gen_date.year, gen_date.month, gen_date.day), 
                                                datetime.now()):
            err_msgs.append("Issue date can't be after current date.")
            invalid = True
            
        if invalid:
            raise forms.ValidationError('\n'.join(err_msgs))
    
class IdForm(ModelForm, DocumentBaseForm):    
    name = ID
    
    birth_date = forms.DateField(label="Issue date", widget=forms.DateInput(attrs={"type":"date"}))
    id_gen_date = forms.DateField(label="Issue date", widget=forms.DateInput(attrs={"type":"date"}))
    id_exp_date = forms.DateField(label="Expiration date", widget=forms.DateInput(attrs={"type":"date"}))
    id_image = forms.FileField(label="Document scan")
    
    class Meta:
        model = IdDocument
        fields = ['id_num', 'heb_first_name', 'heb_last_name']
    
    def required(self, input, name):
        if input is None:
            raise forms.ValidationError(f'{name} required for ID')
    
    def validate_id_num(self, id_num):
        self.required(id_num, 'ID number')
        
        id_num = StringValidator.validate_id_num(id_num)
        if not id_num:
            raise forms.ValidationError('id number (must be valid id number containing 9 digits)')
    
    def validate_age_over_18(self, birth_date):
        self.required(birth_date, 'Birth date')
        age = relativedelta(datetime.now(), birth_date).years >= 18
        if not age:
            raise forms.ValidationError('age (must be over 18)')
        
    def clean(self):
        self.validate_id_num(self.cleaned_data.get('id_num'))
                
        gen_date = self.cleaned_data.get('id_gen_date')
        exp_date = self.cleaned_data.get('id_exp_date')
        
        self.required(gen_date, 'Issue date') 
        self.required(exp_date, 'Expiration date')
        self.required(self.cleaned_data.get('id_image'), 'Document scan')
        
        self.clean_date(gen_date, exp_date)
            
        self.validate_age_over_18(self.cleaned_data.get('birth_date'))
        return self.cleaned_data      

class DrivingLicenseForm(DocumentBaseForm):   
    name = DRIVING_LICENSE
    driving_license_first_name = forms.CharField(max_length=20, label="First name as appeared in document (english)", required=False, validators=[NameValidator.validate_eng_name])
    driving_license_heb_first_name = forms.CharField(max_length=20, label="First name as appeared in document (hebrew)", required=False, validators=[NameValidator.validate_heb_name])
    driving_license_last_name = forms.CharField(max_length=20, label="Last name as appeared in document (english)", required=False, validators=[NameValidator.validate_eng_name])
    driving_license_heb_last_name = forms.CharField(max_length=20, label="Last name as appeared in document (hebrew)", required=False, validators=[NameValidator.validate_heb_name])
    address = forms.CharField(max_length=30, label="Address as appeared in document (hebrew)", required=False)
    license_num = forms.CharField(max_length=8, label="License number", required=False)
    unique_num = forms.CharField(max_length=4, label="Unique number", required=False, validators=[LicenseValidators.unique_num_validator])
     
    driving_license_gen_date = forms.DateField(label="Issue date", required=False, widget=forms.DateInput(attrs={"type":"date"}))
    driving_license_exp_date = forms.DateField(label="Expiration date", required=False, widget=forms.DateInput(attrs={"type":"date"}))
    driving_license_image = forms.FileField(label="Document scan", required=False)
        
        
class PassportForm(DocumentBaseForm):  
    name = PASSPORT
    passport_first_name = forms.CharField(max_length=20, label="First name as appeared in document (english)", required=False, validators=[NameValidator.validate_eng_name])
    passport_last_name = forms.CharField(max_length=20, label="Last name as appeared in document (english)", required=False, validators=[NameValidator.validate_eng_name])
    passport_num = forms.CharField(max_length=8, label="Passport number", required=False)
    gender = forms.ChoiceField(required=False, label="Gender", choices = (("1", "Male"),("2", "Female")))
    
    passport_gen_date = forms.DateField(label="Issue date", required=False, widget=forms.DateInput(attrs={"type":"date"}))
    passport_exp_date = forms.DateField(label="Expiration date", required=False, widget=forms.DateInput(attrs={"type":"date"}))
    passport_image = forms.FileField(label="Document scan", required=False)