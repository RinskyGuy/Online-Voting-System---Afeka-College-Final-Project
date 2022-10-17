from django import forms 
from django.forms import ModelForm
from .models import Voter

class VotersForm(forms.Form):
    voters = forms.FileField()
    
class VoterImagesForm(forms.Form):
    id_face_image = forms.FileField(label="ID face image")
    driving_license_face_image = forms.FileField(label="Driving license face image", required=False)
    passport_face_image = forms.FileField(label="Passport face image", required=False)
   
class VoterForm(ModelForm):
    class Meta:
        model = Voter
        exclude = ['unique_num', 'id_doc', 'driving_license_doc', 'passport_doc', 'election']

class VoterLoginForm(forms.ModelForm):
    unique_code = forms.CharField(label='', widget=forms.PasswordInput(attrs={"size":80}))

    class Meta:
        model = Voter
        fields = [
            'unique_code'
        ]
       
class VoterDocUploadForm(forms.Form):
    doc_scan = forms.ImageField(label='')
    
class FrameImageForm(forms.Form):
    frame = forms.ImageField(label='')