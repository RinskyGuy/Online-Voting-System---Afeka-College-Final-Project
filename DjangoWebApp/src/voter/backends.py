from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Voter

class VoterBackend(ModelBackend):

    def authenticate(self, request, **kwargs):
        unique_num = kwargs['unique_num']
        try:
            voter = Voter.objects.get(unique_num=unique_num)
            return voter.user
        except Voter.DoesNotExist:
            pass