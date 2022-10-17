from django.contrib.admin.apps import AdminConfig

class CustomAdminConfig(AdminConfig):
    default_site = 'secure_voting_system.admin.CustomAdminSite'