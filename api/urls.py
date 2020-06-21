from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('sendmail', views.SendMail.as_view()),
    path('sendmailwithtemplate', views.SendMailWithTemplate.as_view()),
    path('register', views.UserCreate.as_view(), name='account-create'),
    path('sendscheduledmail', views.SendScheduledMail.as_view()),
	path('resetpassword', views.PasswordReset.as_view(), name='reset_password'),
	
]