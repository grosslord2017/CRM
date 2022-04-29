from django.contrib import admin
from .models import Profile, Task


# Register your models here.

class ProfileAdmin(admin.ModelAdmin):

    list_display = ('user', 'name', 'surname', 'department', 'position', 'telephone')
    list_display_links = ('user', 'name', 'surname')
    search_fields = ('surname', 'telephone')

class TaskAdmin(admin.ModelAdmin):

    list_display = ('subject', 'final_date', 'status_completed', 'task_manager', 'executor_id')
    list_display_link = ('subject')
    search_field = ('final_date')
    list_filter = ('final_date', 'status_completed')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Task, TaskAdmin)


