from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_crm, name='home_crm'),

    path('login-google/', include('social_django.urls', namespace='social')), #google
    # path('logout-google/', views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),

    path('logout/', views.user_logout, name='logout'),
    path('login/', views.user_login, name='login'),
    path('registration/', views.user_registration, name='registration'),
    path('registration_profile/', views.create_profile, name='create_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('task/', views.task_create, name='task_form'),
    path('my_tasks/', views.my_tasks, name='my_tasks'),
    path('my_task/<int:pk>/', views.my_task_inside, name='my_task_inside'),
    path('supervising_tasks/', views.supervising_tasks, name='supervising_tasks'),
    path('supervising_tasks/<int:pk>/', views.supervising_task_inside, name='supervising_task_inside'),
    path('archive/', views.views_archive, name='archive'),
    path('completed_task/<int:pk>/', views.views_completed_task, name='completed_task'),
    path('choice_position', views.choice_position, name='choice_position'),
    path('choice_profile', views.choice_profile, name='choice_profile'),
    path('viewing_route', views.viewing_route, name='viewing_route'),
    path('create_workplace/', views.create_workplace, name='create_workplace'),
    path('change_password/', views.change_password, name='change_password'),
    path('restore_account/', views.restore_account, name='restore_account'),
    path('user_management/', views.user_management, name='user_management'),
    path('admin_redactor/<int:pk>/', views.admin_redactor, name='admin_redactor'),

]
