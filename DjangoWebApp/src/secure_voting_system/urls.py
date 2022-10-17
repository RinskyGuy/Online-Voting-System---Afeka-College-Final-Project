"""secure_voting_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from vote.views import confirm_vote_view
from election.views import create_election_view
#from document.views import upload_documents_view
from voter.views import UploadVotersView, GenerateVoterView
from candidate.views import UploadCandidatesView, ChooseCandidateView

urlpatterns = [
    path('', include('voter.urls')),
    path('auth/doc_scan', include('voter.urls')),
    path('auth/face_recognition', include('voter.urls')),
    path('video_stream', include('voter.urls')),
    path('vote', ChooseCandidateView.as_view()),
    path('confirmation', confirm_vote_view, name="vote_confirmation"),
    path('admin/create_election/elections_time', create_election_view),
    path('admin/create_election/upload_candidates',  UploadCandidatesView.as_view()),
    path('admin/create_election/upload_voters_data', UploadVotersView.as_view()),
    path('admin/voter/voter/add/generatedata', GenerateVoterView.as_view()),
    path('admin/', admin.site.urls),
]
