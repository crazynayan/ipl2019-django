from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('member_upload/', views.member_upload, name='member_upload'),

    path('players/', views.player_list, name='player_list'),
    path('player_upload/', views.player_upload, name='player_upload'),

    path('my_players/', views.my_player, name='my_player_list'),
    path('my_players/<int:pk>/remove/', views.remove_player, name='remove_player'),
    path('all_players/', views.all_player, name='all_player_list'),

    path('available_players/', views.available_player, name='available_player_list'),
    path('available_players/<int:pk>/invite/', views.invite_player, name='invite_player'),

    path('bid_player/', views.bid_player, name='bid_player'),

    path('player_ownership_upload/', views.player_ownership_upload, name='player_ownership_upload'),
    path('update_scores/', views.update_scores, name='update_scores'),
    path('player_removal/', views.player_removal, name='player_removal'),
    path('reset/', views.reset, name='reset'),
]