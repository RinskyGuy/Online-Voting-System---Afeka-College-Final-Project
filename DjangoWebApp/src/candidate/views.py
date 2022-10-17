import hashlib
import subprocess
from django.shortcuts import render
from django.http import HttpResponseRedirect
from voter.utils import case_admin, check_key_in_session
from .forms import CandidateListForm, GetCandidateForm
from .models import Candidate
from PIL import Image 
from utils.files_handler import save_image
from django.views import View
from vote.models import Vote
from django.contrib import admin

class UploadCandidatesView(View):
    def get(self, request, *args, **kwargs):
        if not admin.site.has_election(request):
            form = CandidateListForm()
            context = {'form':form}
            
            return render(request, "upload_candidates.html", context)
        return HttpResponseRedirect('/admin')
    
    def post(self, request, *args, **kwargs):
        form = CandidateListForm(request.POST, request.FILES)
        candidates_imgs = request.FILES.getlist('images')
        
        if form.is_valid():
            candidates_csv = form.cleaned_data['candidates_list']
            Candidate.save_from_csv(candidates_csv)
            
            for img in candidates_imgs:
                save_image(Image.open(img), Candidate.get_images_dir(), img.name)
                
            return HttpResponseRedirect('/admin')

        self.get(request)

class ChooseCandidateView(View):
    def get(self, request, *args, **kwargs):
        print(request.session)
        case_admin(request)
        if admin.site.has_election(request):
            if check_key_in_session(request, 'voter_unique_code') and check_key_in_session(request, 'doc_approved') and check_key_in_session(request, 'recognized'):
                if request.session['doc_approved'] and request.session['recognized']:
                    hashed_unique_code = Vote.gen_hashed_unique_num(request.session['voter_unique_code'])
                    vote = Vote.get(hashed_unique_code) 
                    if vote is not None:
                        if not vote.has_voted:
                            all_candidates = Candidate.objects.all()
                            form = GetCandidateForm()             
                            context = {'all_candidates': all_candidates, 'form': form, 'msg':None}
                            return render(request, "list_candidates.html", context)
                        else:
                            return HttpResponseRedirect('/confirmation')
        return HttpResponseRedirect('/')
    
    def post(self, request, *args, **kwargs):
        if 'voter_unique_code' in request.session.keys() and request.session['doc_approved'] and request.session['recognized']:
            unique_code = request.session['voter_unique_code']
            hashed_unique_code = Vote.gen_hashed_unique_num(request.session['voter_unique_code'])
            vote = Vote.get(hashed_unique_code) 
            if vote is not None:
                if not vote.has_voted:
                    form = GetCandidateForm(request.POST)
                    if form.is_valid():
                        val = form.cleaned_data.get("confirm_btn")
                        vote.has_voted = True
                        check = subprocess.run(['./ApplyVote.exe', str(val)], capture_output=True, text=True)
                        print(check.returncode)
                        #if check.returncode == 0:
                            #TODO: SQL hasProcessed = true
                            #vote.has_processed = True
                            #TODO: Return Codes
                        candidate = Candidate.objects.get(pk=val)
                        name_field_object = Candidate._meta.get_field('name')
                        candidate_name = name_field_object.value_from_object(candidate)
                        org_hash_vote = hashlib.sha256(candidate_name.encode() + unique_code.encode()).hexdigest()

                        prefixes = vote.get_dict('candidates_prefix')
                        prefix = prefixes[val-1]
                        if prefix == -1:
                            vote.vote = org_hash_vote[::-1][0:6]
                        else:
                            vote.vote=org_hash_vote[prefix:prefix+6]
                        vote.save()
                        return HttpResponseRedirect('/confirmation') ## need to send the specific return code also
                        
                        #else:
                         #   all_candidates = Candidate.objects.all()
                          #  form = GetCandidateForm()             
                           # context = {'all_candidates': all_candidates, 'form': form, 'msg': 'Error occured, please try again.'}
                            #render(request, "list_candidates.html", context)
                        val = -2
                        del(val)
                    
        return HttpResponseRedirect('/')