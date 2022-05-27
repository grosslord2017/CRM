from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_crm, name='home_crm'),
    # path('contact/', views.contact_crm, name='contact_crm'),
    path('logout/', views.user_logout, name='logout'),
    path('login/', views.user_login, name='login'),
    path('registration/', views.user_registration, name='registration'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('task/', views.task_create, name='task_form'),
    path('my_tasks/', views.my_tasks, name='my_tasks'),
    path('my_task/<int:pk>/', views.my_task_inside, name='my_task_inside'),
    path('supervising_tasks/', views.supervising_tasks, name='supervising_tasks'),
    path('supervising_tasks/<int:pk>/', views.supervising_task_inside, name='supervising_task_inside'),
    path('archive/', views.views_archive, name='archive'),
    path('choice_position', views.choice_position, name='choice_position'),
    path('choice-profile', views.choice_profile, name='choice-profile'),
    path('create_workplace/', views.create_workplace, name='create_workplace'),
    path('change_password/', views.change_password, name='change_password'),
    path('restore_account/', views.restore_account, name='restore_account'),
    path('user_management/', views.user_management, name='user_management'),
]
