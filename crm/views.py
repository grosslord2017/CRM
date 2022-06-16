import re
import json
import django.contrib.auth.hashers as hash

from random import randint
from .sender import send_mail
from django.db.models import Q
from django.contrib import messages
from datetime import date, timedelta
from django.http.response import JsonResponse
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .models import Profile, Task, ArchiveTask, Position, Comment, VerifiCode
from django.shortcuts import render, HttpResponseRedirect, Http404, HttpResponse
from .forms import AutorizationForm, UserRegistrationForm, UserEditForm, TaskCreateForm,\
    CommentCreateForm, DepartmentCreateForm, PositionCreateForm, ChangePasswordForm, RestoreAccountForm,\
    CreateNewPass, ProfileEditForm, DepartmentEditForm


def home_crm(request):
    try:
        profile_active_user = Profile.objects.get(user_id=request.user.id)
        user_hot_task = Task.objects.filter(executor_id=profile_active_user,
                                            status_completed=False).order_by('final_date')[:5]
        return render(request, 'crm/home_crm.html', {'profile': profile_active_user,
                                                     'user_hot_task': user_hot_task})
    except:
        return render(request, 'crm/home_crm.html')

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def user_login(request):
    # won't let me log-in again
    if request.user.is_authenticated:
        return Http404

    if request.method == 'POST':
        form = AutorizationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            user = authenticate(username=form_data['username'].lower(), password=form_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    messages.error(request, 'Disabled account')
                    return HttpResponseRedirect('/login/')
            else:
                messages.error(request, 'Invalid login')
                return HttpResponseRedirect('/login/')
    else:
        form = AutorizationForm()
    return render(request, 'crm/login.html', {'form': form})

# переписать под 2 формі что бизбавится от одной громоздкой
def create_profile(request):
    try:
        profil_card = request.user.profile
        return Http404
    except:
        None

    group = Group.objects.all()
    position = Position.objects.all()

    if request.method == 'POST':
        profile_form = ProfileEditForm(request.POST)
        department_form = DepartmentEditForm(request.POST)
        if profile_form.is_valid() and department_form.is_valid():
            profile = profile_form.cleaned_data
            department = department_form.cleaned_data
            Profile.objects.create(
                user=request.user,
                name=profile['name'],
                surname=profile['surname'],
                telephone=profile['telephone'],
                department_id=department['department'].id,
                position_id=department['position'].id,
            )
            messages.success(request, 'Profile card created successfully!')
            return HttpResponseRedirect('/')

    profile_form = ProfileEditForm()
    department_form = DepartmentEditForm()
    return render(request, 'crm/registration_profile.html', {'profile_form': profile_form,
                                                             'department_form': department_form,
                                                             'group': group,
                                                             'position': position})

def user_registration(request):
    if request.user.is_authenticated:
        return Http404

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.cleaned_data
            if user['password'] != user['password2']:
                messages.error(request, 'Passwords don\'t match.')
                return HttpResponseRedirect('/registration/')

            if not password_security_check(user['password']):
                mes = 'Password must be at least 8 characters long, ' \
                      'contain uppercase and lowercase characters, and contain numbers'
                messages.error(request, mes)
                return HttpResponseRedirect('/registration/')

            if verification_email(user['email']):
                messages.error(request, 'Email is already used')
                return HttpResponseRedirect('/registration/')

            new_user = User.objects.create(
                username=user['username'].lower(),
                email=user['email']
            )
            new_user.set_password(user['password'])
            new_user.save()
            messages.success(request, 'user create success')
            return render(request, 'crm/registration_done.html', {'new_user': new_user})
        else:
            messages.error(request, user_form.errors.as_text())
        return HttpResponseRedirect('/registration/')
    user_form = UserRegistrationForm()
    return render(request, 'crm/registration.html', {'user_form': user_form})

@login_required
def edit_profile(request):
    if not get_or_none(Profile, user_id=request.user.id):
        return HttpResponseRedirect('/')

    department = Group.objects.all()

    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_date = user_form.cleaned_data
            profile_date = profile_form.cleaned_data

            if User.objects.filter(email=user_date['email']).exclude(id=request.user.id):
                messages.error(request, 'This email is already used')
                return HttpResponseRedirect('/edit/')
            if Profile.objects.filter(telephone=profile_date['telephone']).exclude(user_id=request.user.id):
                messages.error(request, 'This telephone is already used')
                return HttpResponseRedirect('/edit/')

            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect('/')

    else:
        try:
            profile_form = ProfileEditForm(instance=request.user.profile)
        except:
            profile_form = ProfileEditForm()

    user_form = UserEditForm(instance=request.user)

    return render(request, 'crm/edit_profile.html', {'user_form': user_form,
                                                     'profile_form': profile_form,
                                                     'depart': department})

@login_required
def task_create(request):
    if not get_or_none(Profile, user_id=request.user.id):
        messages.error(request, 'You don\'t have profile.')
        return HttpResponseRedirect('/')
    group = Group.objects.all()
    date_today = str(date.today())
    date_future = str(date.today() + timedelta(days=365 * 2))
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            date_form = form.cleaned_data
            Task.objects.create(
                subject=date_form['subject'],
                final_date=date_form['final_date'],
                description=date_form['description'],
                task_manager_id=request.user.id,
                executor_id=date_form['executor'].id,
            )

            # create and send notification
            to = Profile.objects.get(id=date_form['executor'].id).user.email
            subject = date_form['subject']
            body = f"ОТ: {request.user.profile.surname} {request.user.profile.name} \n\n {date_form['description']}"
            try:
                send_mail(to, subject, body)
            except:
                messages.error(request, 'Email was not sent')

            return HttpResponseRedirect('/')
    else:
        form = TaskCreateForm()
    return render(request, 'crm/task_form.html', {'form': form, 'date_today': date_today,
                                                  'date_future': date_future, 'group': group})

@login_required
def my_tasks(request):
    if not get_or_none(Profile, user_id=request.user.id):
        return HttpResponseRedirect('/')
    profile = Profile.objects.get(user_id=request.user.id)
    tasks = Task.objects.filter(executor_id=profile).all()

    return render(request, 'crm/my_tasks.html', {'tasks': tasks})

# page in my task
@login_required
def my_task_inside(request, pk):
    task = Task.objects.get(id=pk)
    comment_form = CommentCreateForm()
    group = Group.objects.all()

    if request.method =='POST':
        if request.POST.get('status', False):
            delegate = request.POST.get('position', False)
            # block complete task
            if not delegate:
                task.status_completed = True
                task.save()

                # block answer task completion
                to = User.objects.get(id=task.task_manager.id).email
                subject = 'Re:' + task.subject
                body = f"Пользователь {request.user.profile.surname} {request.user.profile.name} Завершил задачу!"
                try:
                    send_mail(to, subject, body)
                except:
                    messages.error(request, 'Email was not sent')
                return HttpResponseRedirect('/my_tasks/')

            # block delegate task
            else:
                task.executor_id = delegate
                task.save()
                to = Profile.objects.get(id=task.executor_id).user.email
                subject = task.subject
                body = f"Пользователь {request.user.profile.surname} {request.user.profile.name} " \
                       f"перенаправил на Вас задачу {task.subject} \n {task.description}"
                try:
                    send_mail(to, subject, body)
                except:
                    messages.error(request, 'Email was not sent')
            return HttpResponseRedirect('/my_tasks/')
        else:
            # block create comment
            comment_form = CommentCreateForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.cleaned_data
                create_comment = Comment.objects.create(
                    task_fk=task,
                    author=Profile.objects.get(user_id=request.user.id),
                    text=comment['text'],
                )
                create_comment.save()
                return HttpResponseRedirect(f'/my_task/{pk}')
    else:
        # checking the correspondence of the user and the task
        task_and_user_verification(request, task, 'my_task_inside')

    # filtered and output comments
    comments = Comment.objects.filter(task_fk_id=pk).order_by('date')[::-1]

    return render(request, 'crm/my_task_inside.html', {'task': task,
                                                       'comment_form': comment_form,
                                                       'comments': comments,
                                                       'group': group})

@login_required
def supervising_tasks(request):
    if not get_or_none(Profile, user_id=request.user.id):
        return HttpResponseRedirect('/')
    user = request.user.id
    tasks = Task.objects.filter(task_manager_id=user).all()
    return render(request, 'crm/supervising_tasks.html', {'tasks': tasks})

@login_required
def supervising_task_inside(request, pk):
    task = Task.objects.get(id=pk)
    comment_form = CommentCreateForm()
    if request.method == 'POST':
        # block check to complete
        if request.POST.get('status', False):
            task_manager = Profile.objects.get(id=task.executor_id)
            archive = ArchiveTask.objects.create(
                date_create=task.date_create,
                subject=task.subject,
                task_manager=task.task_manager.profile.surname,
                executor=task_manager.surname,
                task_id=task.id
            )
            archive.save()
            task.status_completed = True
            task.archived = True
            task.save()
            # task.delete()
            return HttpResponseRedirect(f'/supervising_tasks/')

        # block create comment
        comment_form = CommentCreateForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.cleaned_data
            create_comment = Comment.objects.create(
                task_fk=task,
                author=Profile.objects.get(user_id=request.user.id),
                text=comment['text'],
            )
            create_comment.save()
            return HttpResponseRedirect(f'/supervising_tasks/{pk}')
    else:
        # checking the correspondence of the user and the task
        task_and_user_verification(request, task, 'supervising_task_inside')

    # output comments
    comments = Comment.objects.filter(task_fk_id=pk).order_by('date')[::-1]

    return render(request, 'crm/supervising_task_inside.html', {'task': task,
                                                       'comment_form': comment_form,
                                                       'comments': comments})

def views_archive(request):
    if request.user.is_superuser:
        archive = ArchiveTask.objects.order_by('date_create')

        if request.method == 'POST':
            search = request.POST['search']
            archive = ArchiveTask.objects.filter(Q(date_create__icontains=search) | Q(subject__icontains=search) |
                                            Q(task_manager__icontains=search) | Q(executor__icontains=search) |
                                            Q(date_complete__icontains=search))

        return render(request, 'crm/archive.html', {'archive': archive})
    else:
        raise Http404

@login_required
def views_completed_task(request, pk):
    if not request.user.is_superuser:
        return Http404

    archive_task = ArchiveTask.objects.get(id=pk)
    task = Task.objects.get(id=archive_task.task_id)
    comments = Comment.objects.filter(task_fk_id=archive_task.task_id)[::-1]

    return render(request, 'crm/view_task_in_archive.html', {'task': task, 'comments': comments,
                                                             'archive_task': archive_task})

# ajax in registration template
def choice_position(request):
    department_id = json.loads(request.body).get('depId')
    pos_list = []
    if department_id:
        positions = Position.objects.filter(department_fk=department_id)
        for position in positions:
            pos_l = [position.name, position.id]
            pos_list.append(pos_l)

    return JsonResponse({'pos_l': pos_list})

# ajax in task create and delegate
def choice_profile(request):
    department_id = json.loads(request.body).get('depId')
    task_id = json.loads(request.body).get('taskId')
    positions = Position.objects.filter(department_fk=department_id)
    pos_profile = []

    for position in positions:
        if task_id:
            task = Task.objects.get(id=task_id)
            pos_prof = Profile.objects.filter(~Q(user_id=request.user.id) & ~Q(id=task.task_manager.profile.id),
                                                  position=position.id)
        else:
            pos_prof = Profile.objects.filter(~Q(user_id=request.user.id), position=position.id)

        if pos_prof:
            for pos_p in pos_prof:
                prof = [pos_p.name, pos_p.surname, position.name, pos_p.id]
                pos_profile.append(prof)

    return JsonResponse({'pos_p': pos_profile})

# check if this user has a task, if not - return 404
def task_and_user_verification(request, task, flag):
    session_user_id = request.session['_auth_user_id']
    if flag == 'my_task_inside':
        executor = Profile.objects.get(id=task.executor_id).user.id
        if session_user_id != str(executor):
            raise Http404
    elif flag == 'supervising_task_inside':
        task_manager = task.task_manager_id
        if session_user_id != str(task_manager):
            raise Http404
    else:
        return

# create department and position
def create_workplace(request):
    dep = Group.objects.all()
    if request.method == 'POST':

        form_dep = DepartmentCreateForm(request.POST)
        form_pos = PositionCreateForm(request.POST)
        if not request.POST.get('department_fk', False) and form_dep.is_valid():
            form = form_dep.cleaned_data
            if not get_or_none(Group, name=form['name']):
                Group.objects.create(
                    name=form['name']
                )
                messages.success(request, 'Department create successfully')

                return HttpResponseRedirect('/create_workplace/')
        else:
            if form_pos.is_valid():
                form = form_pos.cleaned_data
                if not get_or_none(Position, name=form['name']):
                    Position.objects.create(
                        department_fk=form['department_fk'],
                        name=form['name']
                    )
                    messages.success(request, 'Position create successfully')
                    return HttpResponseRedirect('/create_workplace/')
    else:
        form_dep = DepartmentCreateForm()
        form_pos = PositionCreateForm()
    return render(request, 'crm/create_workplace.html', {'form_dep': form_dep,
                                                         'form_pos': form_pos,
                                                         'dep': dep})

# user can change the password
@login_required
def change_password(request):
    if get_or_none(User, id=request.user.id).last_name:
        return Http404

    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            pas_form = form.cleaned_data
            if hash.check_password(pas_form['old_password'], user.password):
                if pas_form['new_password'] == pas_form['confirm_password']:
                    if password_security_check(pas_form['new_password']):
                        user.set_password(pas_form['confirm_password'])
                        user.save()
                        return render(request, 'crm/change_user_pass_done.html')
                    else:
                        mes = 'Not strong password.'
                        messages.error(request, mes)
                else:
                    messages.error(request, 'new password and confirm password do not match')
            else:
                messages.error(request, 'wrong old password')
    else:
        form = ChangePasswordForm()

    return render(request, 'crm/change_user_pass.html', {'form': form})

# if forget password you make restore account and create new password
def restore_account(request):
    if request.method == 'POST':
        form_email = RestoreAccountForm(request.POST)
        form_new_passwd = CreateNewPass(request.POST)
        if request.POST.get('email', False) and form_email.is_valid():
            code = randint(10000, 99999)
            form = form_email.cleaned_data
            user = get_or_none(User, email=form['email'])
            if user:
                VerifiCode.objects.create(
                    user_login=user.username,
                    code=code
                )
                to = user.email
                subject = 'Restore you account'
                body = f'Someone is trying to recover your account. If this is not you, please ignore this email. \n'\
                       f'Your login: {user.username} \n'\
                       f'code: {code}'
                send_mail(to, subject, body)

                form_new_passwd = CreateNewPass()
                return render(request, 'crm/verification_code.html', {'form_new_passwd': form_new_passwd})
            else:
                messages.error(request, 'there is no such mail in the database')
        elif request.POST.get('code', False) and form_new_passwd.is_valid():
            form = form_new_passwd.cleaned_data
            confirm = get_or_none(VerifiCode, code=form['code'])
            if confirm:
                user = User.objects.get(username=confirm.user_login)
                if form['new_passwd'] == form['confirm_passwd']:
                    if password_security_check(form['new_passwd']):
                        user.set_password(form['confirm_passwd'])
                        user.save()
                        VerifiCode.objects.filter(user_login=user.username).delete()
                        messages.success(request, 'new password has been set')
                        return HttpResponseRedirect('/')
                    else:
                        messages.error(request, 'Not strong password.')
                else:
                    messages.error(request, 'Passwords do not match')
            else:
                messages.error(request, 'Code doesn\'t work')

            form_new_passwd = CreateNewPass()
            return render(request, 'crm/verification_code.html', {'form_new_passwd': form_new_passwd})

    form_email = RestoreAccountForm()

    return render(request, 'crm/restore_account.html', {'form_email': form_email})

# admin can delete users and rasie up / lower down
def user_management(request):
    all_users = Profile.objects.filter(~Q(user_id=request.user.id))

    if request.method == 'POST':

        if request.POST.get('delete', False) or request.POST.get('permission', False):
            try:
                user = request.POST['delete']
            except:
                user = request.POST['permission']
            user = User.objects.get(username=user)

            if request.POST.get('delete', False):
                user.delete()
            elif request.POST.get('permission', False):
                if user.is_superuser:
                    user.is_superuser = False
                else:
                    user.is_superuser = True
                user.save()

        elif request.POST.get('search', False):
            search = request.POST['search']
            all_users = Profile.objects.filter(Q(telephone__icontains=search) | Q(name__icontains=search) |
                                            Q(surname__icontains=search) | Q(department_id__name__icontains=search) |
                                            Q(position_id__name__icontains=search) |
                                            Q(user_id__username__icontains=search) |
                                            Q(user_id__email__icontains=search)).exclude(Q(user_id=request.user.id))

        elif request.POST.get('edit', False):
            print(request.POST)

            pass

    return render(request, 'crm/user_management.html', {'all_users': all_users})

# if email already used - error
# подобное есть в edit_profile - посмотреть и подправить
def verification_email(email):
    if get_or_none(User, email=email):
        return True
    else:
        return False

# replaces block try/except
def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except:
        return None

def password_security_check(passwd):
    # if len(passwd) < 8:
    #     message = 'Password is to short! Must be at least 8 characters'
    #     return (False, message)
    # elif re.search(r'[a-z]', passwd) and re.search(r'[A-Z]', passwd) and \
    #         re.search(r'\d', passwd) and not re.search(r'\s', passwd):
    #     return True
    # else:
    #     message = 'Password must have large and small characters, and a number.'
    #     return (False, message)

# попробовать добавить проверку на {8, } - минимум символов
    if re.search(r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,}', passwd):
        return True
    else:
        return False

def admin_redactor(request, pk):
    if not request.user.is_superuser:
        return Http404

    group = Group.objects.all()
    position = Position.objects.all()
    profile = Profile.objects.get(user_id=pk)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST)
        profile_form = ProfileEditForm(request.POST)
        department_form = DepartmentEditForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            messages.success(request, 'changes save successfully')
            email = user_form.cleaned_data
            profile_info = profile_form.cleaned_data
            user = User.objects.get(id=pk)
            user.email = email['email']
            user.profile.name = profile_info['name']
            user.profile.surname = profile_info['surname']
            user.profile.telephone = profile_info['telephone']
            if department_form.is_valid():
                department = department_form.cleaned_data
                user.profile.department = department['department']
                user.profile.position = department['position']

            user.save()
            user.profile.save()
            return HttpResponseRedirect('/user_management/')

        elif user_form.is_valid() and profile_form.is_valid():
            pass
        else:
            messages.error(request, 'fields email, name, surname, telephone must not be empty')


    user_form = UserEditForm(instance=profile.user)
    profile_form = ProfileEditForm(instance=profile)
    department_form = DepartmentEditForm()

    return render(request, 'crm/admin_redactor.html', {'user_form': user_form,
                                                       'profile_form': profile_form,
                                                       'department_form': department_form,
                                                       'profile': profile,
                                                        'group': group,
                                                        'position': position})
