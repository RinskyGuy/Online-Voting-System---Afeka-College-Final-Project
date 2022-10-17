from django import forms 

class CastVoteForm(forms.Form):
    confirm_btn = forms.IntegerField()
