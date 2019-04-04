from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberView.as_view(), name='member_list'),
    path('upload-csv/', views.member_upload, name='upload_csv'),
]