from django.shortcuts import render
from django.contrib import admin
from .forms import CreateElectionForm
from django.http import HttpResponseRedirect
from .models import Election
from datetime import datetime

# Create your views here.
def create_election_view(request, *args, **kwargs):
    if not admin.site.has_election(request):
        if request.method == 'POST':
            form = CreateElectionForm(request.POST, request.FILES)
            
            if form.is_valid():
                start_date = form.cleaned_data['start_date']
                start_time = form.cleaned_data['start_time']
                end_date = form.cleaned_data['end_date']
                end_time = form.cleaned_data['end_time']
                
                Election.objects.get_or_create(start_time=datetime.combine(start_date,start_time), 
                                            end_time=datetime.combine(end_date,end_time))
                return HttpResponseRedirect('/admin')
        
        else:
            form = CreateElectionForm()
        
        context = {'form':form}
        return render(request, "election_time.html", context)
    
    else:
        return HttpResponseRedirect('/admin')