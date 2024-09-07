from django.urls import path
from .views import SignupView, LoginView, UserSearchView
from . import views

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('search/',UserSearchView.as_view(),name='user-search'),

    # urls for friend request functionality

    path('send-friend-request/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:pk>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:pk>/', views.reject_friend_request, name='reject_friend_request'),
    path('list-friends/', views.list_friends, name='list_friends'),
    path('list-pending-friend-requests/', views.list_pending_friend_requests, name='list_pending_friend_requests'),
]
