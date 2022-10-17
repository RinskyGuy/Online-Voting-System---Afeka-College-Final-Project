import json
from django.shortcuts import render
from django.contrib import admin
from django.http import HttpResponseRedirect
from .forms import VoterImagesForm, VotersForm, VoterLoginForm, VoterDocUploadForm
from .models import Voter
from django.views import View
from .utils import generate_docs
from utils.files_handler import open_file         
from utils.recognition.document_recognition.doc_recognition import doc_siamese_model
from utils.recognition.document_recognition.doc_ocr import id_ocr, driving_license_ocr, passport_ocr
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT
from utils.session_utils.helper import get_vectors, case_admin, get_voter, get_vote, check_key_in_session
from vote.models import Vote
from utils.files_handler import open_file
import pandas as pd

class UploadVotersView(View):
    def get(self, request, *args, **kwargs):
        if not admin.site.has_election(request):
            voters_form = VotersForm()
            format_msg = "id_num (required), id (required), driving_license (can be None) and passport (can be None)."
            
            docs =      [{'name':'id', 
                        'columns':['id_num', 'heb_first_name', 'heb_last_name', 'birth_date', 'gen_date', 'exp_date'], 
                        'images_input_name':'id_images'},
                        {'name':'driving_license', 
                        'columns':['id_num', 'first_name', 'last_name', 
                                    'heb_first_name', 'heb_last_name', 
                                    'license_num', 'unique_num',
                                    'birth_date', 'gen_date', 'exp_date'], 
                        'images_input_name':'driving_license_images'},
                        {'name':'passport', 
                        'columns':['id_num', 'first_name','last_name','passport_num', 'gender', 'birth_date', 'gen_date', 'exp_date'],
                        'images_input_name':'passport_images'}]
        
            context = {'form':voters_form, 'format_msg':format_msg, 'docs':docs}
            return render(request, "upload_voters.html", context)
        return HttpResponseRedirect('/admin')
    
    def post(self, request, *args, **kwargs):
        voters_form = VotersForm(request.POST, request.FILES)
        if voters_form.is_valid():
            voters_csv = voters_form.cleaned_data['voters']
            voters_df = pd.read_pickle(voters_csv)
            self._create_voter_from_df(voters_df, 
                                       request.FILES.getlist('id_images'), 
                                       request.FILES.getlist('driving_license_images'), 
                                       request.FILES.getlist('passport_images'))
            
        return HttpResponseRedirect('/admin')
  
    def _create_voter_from_df(self, voters_df, id_images, driving_license_images, passport_images):
        for index, row in voters_df.iterrows():
            if row['id'] is not None:
                id_data = row['id']
                id_num = id_data['id_num']
                
                id_scan = self._get_image_by_name(id_images, id_num)            
                driving_license_scan = self._get_image_by_name(driving_license_images, id_num)   
                passport_scan = self._get_image_by_name(passport_images, id_num)
                
                Voter.objects.get_or_create(row, id_scan, driving_license_scan, passport_scan)
                
    def _get_image_by_name(self, images, name):
        for image in images:
            if image.name.startswith(name + '.'):
                return open_file(image)
        
class GenerateVoterView(View):
    def get(self, request, *args, **kwargs):
        form = VoterImagesForm()    
        context = {'form':form}
        return render(request, "generate_voter.html", context)

    def post(self, request, *args, **kwargs):
        generate_docs(request.FILES.getlist("images"))
            
        return HttpResponseRedirect('/admin/voter/voter/add')
                
class LoginView(View):
    def get(self, request, *args, **kwargs):
        print(request.user)
        if not request.user.is_anonymous:
            return render(request, "logout.html", {})
        if admin.site.has_election(request):
            request.session['voter_unique_code'] = None
            request.session['doc_approved'] = False
            request.session['recognized'] = False
            
            #print(request.user.is_anonymous) # dont allow admins to vote from admin account.
            print(request.session.items())
            form = VoterLoginForm()
            
            context = {'form':form, 'hasElection':True, 'err':False}
        
        else: # no election exist
            context = {'hasElection':False}
                
        return render(request, "login.html", context)

    def post(self, request, *args, **kwargs):
        form = VoterLoginForm(request.POST)
        if form.is_valid():
            unique_code = form.cleaned_data['unique_code']
            voter = Voter.get(unique_code)
            
            if voter is not None:
                request.session['voter_unique_code'] = unique_code
                vote = get_vote(request)
                if vote.has_voted:
                    context = {'vote': vote.vote}
            #        print(vote.vote)
                    return render(request, "confirm_vote.html", context)  
                
                #request.session['has_voted'] = vote.has_voted
                return HttpResponseRedirect('auth/doc_scan')
        
        form = VoterLoginForm()
            
        context = {'form':form, 'hasElection':True, 'err':True}
        return render(request, "login.html", context)

     
class DocAuthView(View):
    def _doc_type_prediction(self, voter, doc_scan, debug=False):
        doc_scan = open_file(doc_scan)
        docs = {ID: voter.id_doc, DRIVING_LICENSE:voter.driving_license_doc, PASSPORT:voter.passport_doc}
        doc_vectors = get_vectors(docs, 'doc_vector')
        
        return doc_siamese_model.predict(doc_scan, doc_vectors)
    
    def _text_verification(self, voter, doc_type, doc_scan, debug=False, match='True'):
        ocr = {ID: id_ocr, DRIVING_LICENSE: driving_license_ocr, PASSPORT: passport_ocr}
        doc_scan = open_file(doc_scan)
        #cv2.imwrite(r'C:\Users\Adminuser\Desktop\logs\img.jpg',doc_scan)
        #debug_dir = r'C:\Users\Adminuser\Desktop\logs'
        
        doc_data = None
        #doc_data = get_doc(voter, doc_type)
        if doc_type == ID:
            doc_data = voter.id_doc.get_dict()
        elif doc_type == DRIVING_LICENSE:
            if voter.driving_license_doc is not None:
                doc_data = voter.driving_license_doc.get_dict()
        elif doc_type == PASSPORT:
            if voter.passport_doc is not None:
                doc_data = voter.passport_doc.get_dict()
        
        if doc_type is not None:
            doc_type_str = ' '.join(doc_type.split('_'))
        else:
            doc_type = 'unknown document'
        match = False
        if doc_data is not None:
            #print(doc_data)    
            # doc_ocr.verify_text(doc_scan, doc_data)
            match = ocr[doc_type].text_match(doc_scan, doc_data) #, debug_dir=debug_dir, debug_type='file')
            #log_to_file(f'{avg_distances}\n', staticfiles_storage.path(os.path.join(os.path.join('OCR_distances', match), 'distances.txt')))
            if match: 
                err_msg = None
            else:
                # text verification failed
                err_msg = f'{doc_type_str} scan didn\'t match our data. Please make sure the scan is clear and try again...'
        
        else:
            if doc_type is not None:
                # document predicted not found in database for this voter.
                err_msg = f'{doc_type_str} not found in the system for this voter.'
            else:
                # document didn't match any (siamese document recognition failed)
                err_msg = f'Document recognition failed. Please try another document.'
        return {'passed': match, 'msg': err_msg}
            
    def get(self, request, *args, **kwargs):
        case_admin(request)
        voter = get_voter(request)
        if voter is not None:
            if check_key_in_session(request, 'doc_approved'):
                if not request.session['doc_approved']:
                    form = VoterDocUploadForm()
                    context = {'type':'doc_scan', 'form':form, 'show_disapproved': False}
                    return render(request, "auth.html", context)
                else:
                    return HttpResponseRedirect('face_recognition') #continue from where stopped
        
        return HttpResponseRedirect('/')
    
    def post(self, request, *args, **kwargs):
        case_admin(request)
        print(request.session.items())
        voter = get_voter(request)
        if voter is not None:
            form = VoterDocUploadForm(request.POST, request.FILES)
            if form.is_valid():
                doc_type = self._doc_type_prediction(voter, form.cleaned_data['doc_scan'], debug=True)
                print(doc_type)
                verification_res = self._text_verification(voter, doc_type, form.cleaned_data['doc_scan'], debug=True)
                print(verification_res)
                if verification_res['passed']:
                    request.session['doc_approved'] = True
                    return HttpResponseRedirect('face_recognition')
            
                form = VoterDocUploadForm()
                context = {'type':'doc_scan', 'form':form, 'show_disapproved': True, 'msg': verification_res['msg']}
                return render(request, "auth.html", context)
        return HttpResponseRedirect('/')
    
class FaceAuthView(View):
    def get(self, request, *args, **kwargs):
        video_url = 'videos\zooey.mp4'
        print(request.session.items())
        case_admin(request)
        voter = get_voter(request)
        if voter is not None:
            if check_key_in_session(request, 'doc_approved'):
                if request.session['doc_approved']:
                    if check_key_in_session(request, 'recognized'):
                        if not request.session['recognized']:
                            docs = {ID: voter.id_doc, DRIVING_LICENSE:voter.driving_license_doc, PASSPORT:voter.passport_doc}
                            face_vectors = get_vectors(docs, 'face_vector')
                            context = {'type':'face_recognition', 'face_vectors':json.dumps(face_vectors), 'url':video_url}
                            return render(request, 'auth.html', context)   
                        else:
                            return HttpResponseRedirect('/vote')
        return HttpResponseRedirect('/')

    def post(self, request, *args, **kwargs):
        case_admin(request)
        request.session['recognized'] = True
        return HttpResponseRedirect('/vote')
            
  