from django.contrib import admin
from document.models import DrivingLicenseDocument, IdDocument, PassportDocument
from .models import Voter
from .forms import VoterForm
from document.forms import IdForm, DrivingLicenseForm, PassportForm
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.core.exceptions import PermissionDenied
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.forms.formsets import all_valid
from django.contrib.admin import helpers
from django.utils.translation import gettext as _
from PIL import Image
from vote.models import Vote

IS_POPUP_VAR = '_popup'
TO_FIELD_VAR = '_to_field'
       
class BaseReadOnlyAdminMixin:
    #def has_add_permission(self, request):
    #    return False

    def has_change_permission(self, request, obj=None):
        return False

    #def has_delete_permission(self, request, obj=None):
    #    return False

class VoterModelAdmin(BaseReadOnlyAdminMixin, admin.ModelAdmin):
    # A template for a very customized change view:
    change_form_template = 'voter_change_form.html'
    
    list_display = ["id_doc"]
    
    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs['form'] = VoterForm
        return super().get_form(request, obj, **kwargs)

    def get_osm_info(self):
        # ...
        pass
    
    def _changeform_view(self, request, object_id, form_url, extra_context):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta

        if request.method == 'POST' and '_saveasnew' in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)
        
        fieldsets = self.get_fieldsets(request, obj)
        print(fieldsets)
        ModelForm = self.get_form(
            request, obj, change=not add, fields=flatten_fieldsets(fieldsets)
        )
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            id_form = IdForm(request.POST, request.FILES)
            driving_license_form = DrivingLicenseForm(request.POST, request.FILES)
            passport_form = PassportForm(request.POST, request.FILES)
            
            form_validated = form.is_valid()
            if form_validated and id_form.is_valid():
                created, new_object = Voter.objects.get_or_create(form.cleaned_data)
                if created:
                    IdDocument.objects.get_or_create(new_object, id_form.get_doc_data(), Image.open(id_form.cleaned_data['id_image']))

                try:
                    DrivingLicenseDocument.objects.get_or_create(new_object, driving_license_form.get_doc_data(), Image.open(driving_license_form.cleaned_data['driving_license_image']))
                except:
                    print("Driving license doc not created for voter.")
                
                try:
                    PassportDocument.objects.get_or_create(new_object, passport_form.get_doc_data(), Image.open(passport_form.cleaned_data['passport_image']))
                except:
                    print("Passport doc not created for voter.")
           
            new_object = obj
            
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
           
        else:
            id_form = IdForm()
            driving_license_form = DrivingLicenseForm()
            passport_form = PassportForm()
            
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(request, obj, change=False)
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(fieldsets)
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        adminForm = helpers.AdminForm(
            form,
            list(fieldsets),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj) if add or self.has_change_permission(request, obj) else {},
            readonly_fields,
            model_admin=self)
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        if add:
            title = _('Add %s')
        elif self.has_change_permission(request, obj):
            title = _('Change %s')
        else:
            title = _('View %s')
        context = {
            **self.admin_site.each_context(request),
            'title': title % opts.verbose_name,
            'subtitle': str(obj) if obj else None,
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            'to_field': to_field,
            'media': media,
            'inline_admin_formsets': inline_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'preserved_filters': self.get_preserved_filters(request),
        }

        # Hide the "Save" and "Save and continue" buttons if "Save as New" was
        # previously chosen to prevent the interface from getting confusing.
        if request.method == 'POST' and not form_validated and "_saveasnew" in request.POST:
            context['show_save'] = False
            context['show_save_and_continue'] = False
            # Use the change template instead of the add template.
            add = False

        context.update(extra_context or {})
        
        return self.render_change_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['id_form'] = "id"
        extra_context['driving_license_form'] = "dl"
        extra_context['passport_form'] = "passport"
        #extra_context['osm_data'] = self.get_osm_info()
        
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
        
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['docs'] = [
            {'name': 'ID', 'form': IdForm},
            {'name': 'Driving License', 'form': DrivingLicenseForm},
            {'name': 'Passport', 'form': PassportForm}
        ]
        
        return super().add_view(
            request, form_url, extra_context=extra_context,
        )
    
admin.site.disable_action('delete_selected')

admin.site.register(Voter, VoterModelAdmin)