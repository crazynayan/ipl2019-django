from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_view, name='member_list'),
    path('member_upload/', views.member_upload, name='member_upload'),
    path('players/', views.player_view, name='player_list'),
    path('player_upload/', views.player_upload, name='player_upload'),
    path('my_players/', views.my_player_view, name='my_player_list'),
    path('my_players/<int:pk>/remove/', views.remove_player, name='remove_player'),
    path('all_players/', views.all_player_view, name='all_player_list'),
    path('player_ownership_upload/', views.player_ownership_upload, name='player_ownership_upload'),
]