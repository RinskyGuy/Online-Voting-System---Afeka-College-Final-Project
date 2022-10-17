import ast
import hashlib
import os
from django.db import models
from candidate.models import Candidate
from django.forms.models import model_to_dict
from .validators import unique_code_validator, party_code_validator
from utils.recognition.document_recognition.regex import DateValidator

class VoteQuerySet(models.query.QuerySet):    
    def get_or_create(self, id_data):
        unique_num = Vote.gen_unique_num(id_data['id_num'],
                                         id_data['heb_first_name'], 
                                         id_data['heb_last_name'], 
                                         id_data['birth_date'])
        hashed_unique_num = Vote.gen_hashed_unique_num(unique_num)
        candidate_prefixes, candidate_codes = Vote.gen_candidate_codes(unique_num)
     
        
        vote_in_db = Vote.objects.filter(unique_num=hashed_unique_num)       
        if len(vote_in_db) == 0:
            vote = Vote(unique_num = hashed_unique_num, 
                        candidates_prefix = str(candidate_prefixes))
            
            return True, vote, (unique_num, candidate_codes)
        
        else:
            vote = vote_in_db[0]

        return False, vote, None

class VoteManager(models.Manager):
    def get_queryset(self):
        return VoteQuerySet(self.model)

class Vote(models.Model):
    unique_num = models.CharField(primary_key=True, max_length=64, validators=[unique_code_validator]) # hashed
    candidates_prefix = models.TextField()
    has_voted = models.BooleanField(null=True, default=False)
    has_processed = models.BooleanField(null=True, default=False)
    vote = models.CharField(null=True, max_length=6, validators=[party_code_validator])
    objects = VoteManager()
    
    def get(unique_code):
        try:
            vote = Vote.objects.get(unique_num=unique_code)
            return vote
        except Vote.DoesNotExist:
            return None
    
    def get_dict(self, field):
        vote_data = model_to_dict(self)
        if field == 'candidates_prefix':
            return ast.literal_eval(vote_data[field])
       
        return vote_data[field]
        
    @staticmethod
    def gen_unique_num(id_num, first_name, last_name, birth_date):
        birth_date = DateValidator.date_to_str(birth_date)
        unique_num = hashlib.sha256(id_num.encode() + 
                                    first_name.encode() + 
                                    last_name.encode() + 
                                    birth_date.encode() + 
                                    os.urandom(20)).hexdigest() # to voter
        return unique_num
    
    @staticmethod
    def gen_hashed_unique_num(unique_num):
        hashed_unique_num = hashlib.sha256(unique_num.encode()).hexdigest() # in vote
        return hashed_unique_num
    
        
    @staticmethod
    def gen_candidate_codes(unique_num):
        candidate_prefixes = [] # prefix index for candidate with id i = i-1 
        candidate_codes = {}
        all_candidate = Candidate.objects.all()
        name_field_object = Candidate._meta.get_field('name')
        
        j = 0
        EOS = False
        for candidate in all_candidate:  # - O(l)
            candidate_name = name_field_object.value_from_object(candidate)
            
            candidate_code = hashlib.sha256(candidate_name.encode() + unique_num.encode()).hexdigest()
            while candidate_code[j:j+6] in candidate_codes and not EOS:
                if j+6 == len(candidate_code):
                    EOS = True
                j += 1
            if EOS:
                candidate_codes[candidate_name] = (candidate_code[::-1])[0:6]
                j = -1
            else:
                candidate_codes[candidate_name] = candidate_code[j:j+6]
            
            candidate_prefixes.append(j)
            j = 0
        
        return candidate_prefixes, candidate_codes
        
    