from django.urls import path
from . import views

urlpatterns=[
    path('',views.index,name='index'),
    path('login',views.login_view,name='login'),
    path('logout',views.logout_view,name='logout'),
    path('register',views.register,name='register'),
    path('group/<int:groupID>',views.group,name='group'),
    path('create',views.create,name='create'),
    path('personal',views.personal,name='personal'),

    #api
    path('search',views.search,name='search'),
    path('messages',views.messages,name='messages'),
    path('modify/<int:groupID>',views.modifySetting,name='modifySetting'),
    path('editProfile',views.editProfile,name='editProfile'),
]