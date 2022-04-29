from django import forms
from .models import Profile, Task
from django.contrib.auth.models import User
from django.forms.widgets import DateInput, Textarea, SelectDateWidget


class AutorizationForm(forms.Form):

    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

# This form is also used when editing
class ProfileFillingForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('name', 'surname', 'patronymic', 'telephone', 'department', 'position')

class UserEditForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email',)

class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ('subject', 'final_date', 'description', 'executor')
        # widgets = {
        #     'final_date': SelectDateWidget(),
        #     'description': Textarea(attrs={'cols': 80, 'rows': 20}),
        # }
