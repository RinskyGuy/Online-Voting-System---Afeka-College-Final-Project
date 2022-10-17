from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from election.models import Election
import document.models as documents
from django.conf import settings
from document.models import IdDocument, DrivingLicenseDocument, PassportDocument
from vote.models import Vote
from vote.validators import unique_code_validator, party_code_validator
import os

class VoterQuerySet(models.query.QuerySet):
    def get_or_create(self, data, id_scan, driving_license_scan=None, passport_scan=None):
        id_data = data['id']   
        id_num = data['id_num']
        if id_data is None:
            raise ValueError(f'Missing ID data for {id_num}.')
        if id_scan is None:
            raise ValueError(f'Missing ID scan for {id_num}. Please make sure to upload ID scan for each voter and naming the file with the compatible id number.')

        id_doc = IdDocument.objects.filter(id_num=id_num)
        
        if len(id_doc) == 0:            
            sucess, vote, res = Vote.objects.get_or_create(id_data) 
            if sucess:
                unique_num, candidate_codes = res

                if id_data['id_num'] != id_num:
                    raise ValueError("ID number doesn't match to ID document.")
                sucess, id_doc = documents.IdDocument.objects.get_or_create(id_data, id_scan)
                if not sucess:
                    raise ValueError("ID already exist.")
                voter = Voter(unique_num = unique_num, 
                              id_doc = id_doc,
                              election = Election.objects.all()[0])
                
                driving_license_data = data['driving_license']
                if driving_license_data is not None and driving_license_scan is not None:
                    driving_license_id = driving_license_data['id_num']        
                    if driving_license_id != id_num:
                        raise ValueError(f'ID number of document must match, but got "{id_num}" for id document and "{driving_license_id}" for driving license document.')
                    sucess, driving_license_doc = documents.DrivingLicenseDocument.objects.get_or_create(driving_license_data, driving_license_scan)
                    if not sucess:
                        raise ValueError("Driving license already exist.")
                    voter.driving_license_doc = driving_license_doc
                
                passport_data = data['passport']
                if passport_data is not None and passport_scan is not None:
                    passport_id = passport_data['id_num']
                    if passport_id != id_num:
                        raise ValueError(f'ID number of document must match, but got "{id_num}" for id document and "{passport_id}" for passport document.')                    
                    sucess, passport_doc = documents.PassportDocument.objects.get_or_create(passport_data, passport_scan)
                    if not sucess:
                        raise ValueError("Passport already exist.")
                    voter.passport_doc = passport_doc
                else:
                    passport_doc = None
                
                # save voter
                voter.save()
                
                # save vote
                vote.save()
                
                # generate voter card
                Voter.gen_voter_card(id_num, unique_num, candidate_codes)
        else:
            voter = None
                
        return voter

class VoterManager(models.Manager):
    def get_queryset(self):
        return VoterQuerySet(self.model)

class Voter(models.Model):
    unique_num = models.CharField(primary_key=True, max_length=64, validators=[unique_code_validator])
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    
    id_doc  = models.OneToOneField(IdDocument, on_delete=models.CASCADE)
    driving_license_doc = models.OneToOneField(DrivingLicenseDocument, on_delete=models.CASCADE, null=True, blank=True)
    passport_doc = models.OneToOneField(PassportDocument, on_delete=models.CASCADE, null=True, blank=True)
    objects = VoterManager()
    
    def __str__(self):
         return self.id_doc.id_num
     
    def get(unique_code):
        try:
            voter = Voter.objects.get(pk=unique_code)
            return voter
        except Voter.DoesNotExist:
            return None
        
    def gen_voter_card(id_num, unique_num, candidate_codes):
        if len(set(candidate_codes)) != len(candidate_codes):
            raise ValueError("Party codes should be unique, but got collision.")
        for candidate_code in list(candidate_codes.values()):
            if not party_code_validator(candidate_code):
                raise ValueError(f'Party code should be a hexadecimal string of size 6, but got {candidate_code}.')
            
            
        if not os.path.exists(settings.VOTERS_CSV_PATH):
            dir_path = os.path.split(settings.VOTERS_CSV_PATH)[0]
            os.mkdir(dir_path)
        
        voter_data = {'id':id_num, 'unique_num':unique_num}
        voter_data.update(candidate_codes)
        
        with open(settings.VOTERS_CSV_PATH, 'a') as f:
            f.write(str(voter_data)+'\n')
            
@receiver(post_delete, sender=Voter)
def auto_delete_all_related_with_voter(sender, instance, **kwargs):
    # delete related vote
    unique_num = instance.unique_num
    vote = Vote.objects.filter(unique_num=Vote.gen_hashed_unique_num(unique_num))[0]
    vote.delete()
    
    # delete related id
    instance.id_doc.delete()
    # delete related driving license
    if instance.driving_license_doc is not None:
        instance.driving_license_doc.delete()
    # delete related passport
    if instance.passport_doc is not None:
        instance.passport_doc.delete()