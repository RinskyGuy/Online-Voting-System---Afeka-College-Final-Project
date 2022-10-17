from django.urls import path
from django.views.i18n import JavaScriptCatalog
from .views import create_election_view

urlpatterns = [
     path("jsi18n", JavaScriptCatalog.as_view(), name="js-catlog"),
     path('admin/create_election/elections_time', create_election_view),
]
