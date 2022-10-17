from django.urls import path
from .views import LoginView, DocAuthView, FaceAuthView

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('auth/doc_scan', DocAuthView.as_view(), name='auth'),
    path('auth/face_recognition', FaceAuthView.as_view(), name='auth'),
]