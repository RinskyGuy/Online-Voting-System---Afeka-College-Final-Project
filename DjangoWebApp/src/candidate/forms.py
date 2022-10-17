from django import forms 
from django.forms import ModelForm
from .models import Candidate

class CandidateListForm(forms.Form):
    candidates_list = forms.FileField(label='')
    
class GetCandidateForm(forms.Form):
    confirm_btn = forms.IntegerField()
    
class CandidateModelForm(ModelForm):    
    image = forms.FileField(label="Candidate image", required=False)
    class Meta:
        model = Candidate
        exclude  = ['election', 'img_name']