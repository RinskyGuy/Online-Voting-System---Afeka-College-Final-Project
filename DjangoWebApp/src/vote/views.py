from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Vote

# Create your views here.  
def confirm_vote_view(request, *args, **kwargs):
    if 'voter_unique_code' in request.session.keys():
        hashed_unique_code = Vote.gen_hashed_unique_num(request.session['voter_unique_code'])
        vote = Vote.get(hashed_unique_code) 
        if vote.has_voted:
            context = {'vote': vote.vote}
            print(vote.vote)
            return render(request, "confirm_vote.html", context)
    return HttpResponseRedirect('/')