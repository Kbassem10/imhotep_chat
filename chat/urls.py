from django.urls import path, include
from .auth import auth
from . import messages, user_profile, views, friends
from django.views.generic import TemplateView

urlpatterns = [
    # #the landing page URL
    # path("", views.landing_page, name="landing_page"),

    #the register url
    path("register/", auth.register, name="register"),
    #login url
    path("login/", auth.user_login, name="login"),
    #logout url
    path("logout/", auth.user_logout, name="logout"),
    
    #URL to activate the users account with the Email
    path('activate/<uidb64>/<token>/', auth.activate, name='activate'),

    #URLs for the forget password
    path('password_reset/', auth.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    #URLs for google login
    path('google/login/', auth.google_login, name='google_login'),
    path('google/callback/', auth.google_callback, name='google_callback'),
    path('google/handle-username/', auth.add_username_google_login, name='add_username_google_login'),

    #Test URL for the websockets
    path('websocket-test/', TemplateView.as_view(template_name='websocket_test.html'), name='websocket_test'),

    #Main Page URL
    path('main-menu/', messages.main, name='main_menu'),

    #Chat-related URLs
    path('start-chat/', messages.start_chat, name='start_chat'),
    path('get-messages/<int:chat_room_id>/', messages.get_messages, name='get_messages'),

    #add new friend URL
    path('add-friend/', friends.add_friend, name='add_friend'),
    path('search-user/', friends.search_user, name='search_user'),
    path('accept-friend-request/', friends.accept_friend_request, name='accept_friend_request'),
    path('get-friends/', friends.get_friends, name='get_friends'),
    path('get-friend-requests/', friends.get_friend_requests, name='get_friend_requests'),
    path('block-friend/', friends.block_friend, name='block_friend'),
    path('remove-friend/', friends.remove_friend, name='remove_friend'),
    path('search-friend/', friends.search_friend, name='search_friend'),

    # Add this to your urlpatterns list
    # path('update-profile/', user_profile.update_profile, name='update_profile'),
    # path('password_change/', user_profile.CustomPasswordChangeView.as_view(), name='password_change'),
    # path('password_change/done/', user_profile.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    # path('activate-profile-update/<str:uidb64>/<str:token>/<str:new_email>/', user_profile.activate_profile_update, name='activate_profile_update'),

    # Terms and Privacy pages
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
]
