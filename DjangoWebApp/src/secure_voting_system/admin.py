from multiprocessing import context
from django.contrib import admin
from django.urls import path
from election.models import Election
from candidate.models import Candidate
from voter.models import Voter

class CustomAdminSite(admin.AdminSite):
   # def get_urls(self):
   #     urls = super().get_urls()
   #     new_urls = [path('admin/create_election/', create_election_view)]
   #     return urls+new_urls
        
    def each_context(self, request):
        context = super().each_context(request)
        
        if len(Election.objects.all())>0:
            context["electionCreated"] = True
            
            if len(Candidate.objects.all())>0:
                context["candidatesCreated"] = True
                if len(Voter.objects.all())>0:
                    context["votersCreated"] = True

            
            #if len(Candidate.objects.all())>0 and len(Voter.objects.all())>0:
            #    context["electionDataUploaded"] = True
            #else:
            #    context["electionDataUploaded"] = False
        else:
            context["electionCreated"] = False
        
        print(context)
        print('elections: ', len(Election.objects.all()))
        print('candidates: ', len(Candidate.objects.all()))
        print('voters: ', len(Voter.objects.all()))
        return context
    
    def has_election(self, request):
        site_context = admin.site.each_context(request)
        if self._check_context(site_context, 'electionCreated') and self._check_context(site_context, 'candidatesCreated') and self._check_context(site_context, 'votersCreated'):
            return True
        return False
    
    def _check_context(self, context, field):
        if field in context:
            return context[field]
        
# Register your models here.
CustomAdminSite.index_template = "new_index.html"