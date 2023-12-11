"""
URL configuration for webapps project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from roulette import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home_page, name='home'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('game/', views.game_page, name='game'),
    path('profile/', views.profile, name='profile'),
    path('pre-game/', views.pre_game_page),
    path('create-payment-intent/', views.create_payment),
    path('logout', auth_views.logout_then_login, name='logout'),
    path('subtract_balance/', views.subtract_balance, name='subtract_balance'),
    path('add_balance/', views.add_balance, name='add_balance'),
    path('place_bet', views.place_bet, name='place_bet'),
    # path('get_user_data', views.get_user_data, name='get_user_data'),
    # path('get_users', views.get_users, name='get_users'),
    # path('get_bets', views.get_bets, name='get_bets'),
    path('', views.home_page),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
