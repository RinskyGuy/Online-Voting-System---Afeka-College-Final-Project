from urllib import request
from django.contrib import admin
from .models import Election
from candidate.models import Candidate

class BaseReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    #def has_change_permission(self, request, obj=None):
    #    return False

    #def has_delete_permission(self, request, obj=None):
    #    return False
        
class ElectionModelAdmin(BaseReadOnlyAdminMixin, admin.ModelAdmin):
    def delete_model(self, request, obj=None):
        admin.site.each_context(request)
        Candidate.delete_all_images()
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset=None):
        admin.site.each_context(request)
        Candidate.delete_all_images()
        return super().delete_queryset(request, queryset)
    
    def save_model(self, request, obj=None, form=None, change=None):
        super().save_model(request, obj, form, change)
        admin.site.each_context(request)

admin.site.register(Election, ElectionModelAdmin)