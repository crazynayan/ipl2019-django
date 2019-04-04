from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberView.as_view(), name='member_list'),
]