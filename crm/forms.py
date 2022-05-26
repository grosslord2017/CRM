from django import forms
from .models import Profile, Task, Comment, Position
from django.contrib.auth.models import User, Group
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
        fields = ('name', 'surname', 'telephone', 'department', 'position')

class UserEditForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email',)

class TaskCreateForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ('subject', 'final_date', 'description', 'executor')
        # widgets = {
        #     'final_date': SelectDateWidget(),
        #     'description': Textarea(attrs={'cols': 80, 'rows': 20}),
        # }

class CommentCreateForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 5})
        }

class DepartmentCreateForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ('name',)

class PositionCreateForm(forms.ModelForm):

    class Meta:
        model = Position
        fields = ('department_fk', 'name')

class ChangePasswordForm(forms.Form):

    old_password = forms.CharField(label='Old password', widget=forms.PasswordInput)
    new_password = forms.CharField(label='New password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Repeat new password', widget=forms.PasswordInput)

class RestoreAccountForm(forms.Form):

    email = forms.EmailField(label='Email')

class CreateNewPass(forms.Form):

    code = forms.CharField(required=True)
    new_passwd = forms.CharField(label='New password', widget=forms.PasswordInput, required=True)
    confirm_passwd = forms.CharField(label='Repeat new password', widget=forms.PasswordInput, required=True)
