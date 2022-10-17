from django import forms 
from datetime import datetime
from utils.recognition.document_recognition.regex import DateValidator

class CreateElectionForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type":"time"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type":"time"}))

    def clean(self):
        # data from the form is fetched using super function
        super(CreateElectionForm, self).clean()
        
        # extract the fields from the data
        start_date = self.cleaned_data.get('start_date')
        start_time = self.cleaned_data.get('start_time')
        end_date = self.cleaned_data.get('end_date')
        end_time = self.cleaned_data.get('end_time')
        
        err_msgs = []
        invalid = False
        if not DateValidator.is_before(datetime(start_date.year, start_date.month, start_date.day,
                                                start_time.hour, start_time.minute, start_time.second), 
                                                datetime(end_date.year, end_date.month, end_date.day, 
                                                end_time.hour, end_time.minute, end_time.second)):
            err_msgs.append("Elections end time can't be before start time.")
            invalid = True
            
        if not DateValidator.is_before(datetime.now(),
                                               datetime(start_date.year, start_date.month, start_date.day,
                                                start_time.hour, start_time.minute, start_time.second)):
            err_msgs.append("Elections start time can't be before current time.")
            invalid = True
            
        if not DateValidator.is_before(datetime.now(), 
                                               datetime(end_date.year, end_date.month, end_date.day, 
                                                end_time.hour, end_time.minute, end_time.second)):
            err_msgs.append("Elections end time can't be before current time.")
            invalid = True
            
        if invalid:
            raise forms.ValidationError('\n'.join(err_msgs))
        
        return self.cleaned_data