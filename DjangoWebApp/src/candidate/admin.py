from django.contrib import admin

from candidate.forms import CandidateModelForm
from .models import Candidate

class BaseReadOnlyAdminMixin:
    #def has_add_permission(self, request):
    #    return False

    #def has_delete_permission(self, request, obj=None):
    #    return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
class CandidateModelAdmin(BaseReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "info")
    form = CandidateModelForm

admin.site.register(Candidate, CandidateModelAdmin)