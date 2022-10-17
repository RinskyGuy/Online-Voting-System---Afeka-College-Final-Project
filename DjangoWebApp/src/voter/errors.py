from .models import Voter

def get_voter(unique_code):
    try:
        voter = Voter.objects.get(pk=unique_code)
    except Voter.DoesNotExist:
        pass
        #raise Http404("the obj does not exist.")