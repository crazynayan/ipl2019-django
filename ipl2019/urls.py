from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_view, name='member_list'),
    path('member_upload/', views.member_upload, name='member_upload'),
    path('players/', views.player_view, name='player_list'),
    path('player_upload/', views.player_upload, name='player_upload'),
]