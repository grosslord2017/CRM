import json
import django.contrib.auth.hashers as hash
from datetime import date
from random import randint
from .sender import send_mail
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .models import Profile, Task, ArchiveTask, Position, Comment, VerifiCode
from django.shortcuts import render, HttpResponseRedirect, HttpResponse, Http404
from .forms import AutorizationForm, UserRegistrationForm, UserEditForm, ProfileFillingForm, TaskCreateForm,\
    CommentCreateForm, DepartmentCreateForm, PositionCreateForm, ChangePasswordForm, RestoreAccountForm,\
    CreateNewPass


# Create your views here.

def home_crm(request):
    try:
        profile_active_user = Profile.objects.get(user_id=request.user.id)
        user_hot_task = Task.objects.filter(executor_id=profile_active_user,
                                            status_completed=False).order_by('final_date')[:5]
        return render(request, 'crm/home_crm.html', {'profile': profile_active_user,
                                                     'user_hot_task': user_hot_task})
    except:
        return render(request, 'crm/home_crm.html')

@login_required
def contact_crm(request):
    all_employees = Profile.objects.all()
    return render(request, 'crm/contact_crm.html', {'employees': all_employees})

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def user_login(request):
    if request.user.is_authenticated:
        return Http404

    if request.method == 'POST':
        form = AutorizationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            user = authenticate(username=form_data['username'], password=form_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = AutorizationForm()
    return render(request, 'crm/login.html', {'form': form})

def user_registration(request):
    if request.user.is_authenticated:
        return Http404

    group = Group.objects.all()
    position = Position.objects.all()
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_filling_form = ProfileFillingForm(request.POST)
        if user_form.is_valid() and user_filling_form.is_valid():

            if not verification_email(request.POST['email']):

                profile = user_filling_form.cleaned_data
                # Create a new user object but avoid saving it yet
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()
                # create empty profile for new user (user=new_user) - привязка по id к созданому юзеру
                # Create the user profile
                Profile.objects.create(
                    user=new_user,
                    name=profile['name'],
                    surname=profile['surname'],
                    patronymic=profile['patronymic'],
                    telephone=profile['telephone'],
                    department_id=profile['department'].id,
                    position_id=profile['position'].id,
                )
                return render(request, 'crm/registration_done.html', {'new_user': new_user})
            else:
                messages.error(request, 'emeil is already in use')
    else:
        user_form = UserRegistrationForm()
        user_filling_form = ProfileFillingForm()
    return render(request, 'crm/registration.html', {'user_form': user_form,
                                                     'user_filling_form': user_filling_form,
                                                     'group': group,
                                                     'position': position})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        try:
            profile = request.user.profile
        except:
            Profile.objects.create(
                    name=request.POST['name'],
                    surname=request.POST['surname'],
                    patronymic=request.POST['patronymic'],
                    telephone=request.POST['telephone'],
                    department_id=None,
                    position_id=None,
                    user=request.user
                )
            user_form.save()
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect('/')

        profile_form = ProfileFillingForm(instance=profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect('/')
        elif user_form.is_valid() and not profile_form.is_valid():
            user_form.save()
            if request.POST['department'] == '0':
                profile = Profile.objects.get(user_id=request.user.id)
                profile.name = request.POST['name']
                profile.surname = request.POST['surname']
                profile.patronymic = request.POST['patronymic']
                profile.telephone = request.POST['telephone']
                profile.department = profile.department
                profile.position = profile.position
                profile.save()
                messages.success(request, 'Profile updated successfully')
                return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        try:
            profile = request.user.profile
            profile_form = ProfileFillingForm(instance=profile)
        except:
            profile_form = ProfileFillingForm()

    department = Group.objects.all()

    return render(request, 'crm/edit_profile.html', {'user_form': user_form,
                                                     'profile_form': profile_form,
                                                     'depart': department})

@login_required
def task_create(request):
    group = Group.objects.all()
    date_today = str(date.today())
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
    return render(request, 'crm/task_form.html', {'form': form, 'date': date_today, 'group': group})

@login_required
def my_tasks(request):
    profile = Profile.objects.get(user_id=request.user.id)
    tasks = Task.objects.filter(executor_id=profile).all()

    # подумать как вытащить дату завершения таска и прописать ее на странице my_task

    return render(request, 'crm/my_tasks.html', {'tasks': tasks})

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
    user = request.user.id
    tasks = Task.objects.filter(task_manager_id=user).all()
    return render(request, 'crm/supervising_tasks.html', {'tasks': tasks})

@login_required
def supervising_task_inside(request, pk):
    task = Task.objects.get(id=pk)
    comment_form = CommentCreateForm()
    if request.method == 'POST':
        # block create comment
        if request.POST.get('status', False):
            task_manager = Profile.objects.get(id=task.executor_id)
            archive = ArchiveTask.objects.create(
                date_create=task.date_create,
                subject=task.subject,
                task_manager=task.task_manager.profile.surname,
                executor=task_manager.surname,
                description=task.description
            )
            archive.save()
            task.delete()
            return HttpResponseRedirect(f'/supervising_tasks/')

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
        return render(request, 'crm/archive.html', {'archive': archive})
    else:
        raise Http404

# ajax in registration template
def choice_position(request):
    department_id = json.loads(request.body).get('depId')
    if department_id:
        positions = Position.objects.filter(department_fk=department_id)
        pos_list = []
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

# проверяем есть ли запрошеная задача у текущего пользователя
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

@login_required
# user can change the password
def change_password(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid:
            if hash.check_password(request.POST['old_password'], user.password):
                if request.POST['new_password'] == request.POST['confirm_password']:
                    user.set_password(request.POST['confirm_password'])
                    user.save()
                    return render(request, 'crm/change_user_pass_done.html')
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
            print(code)
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
                # send_mail(to, subject, body)

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
                    user.set_password(form['confirm_passwd'])
                    user.save()
                    VerifiCode.objects.filter(user_login=user.username).delete()
                    messages.success(request, 'new password has been set')
                    return HttpResponseRedirect('/')
                else:
                    messages.error(request, 'passwords do not match')
            else:
                messages.error(request, 'code doesn\'t work')

            form_new_passwd = CreateNewPass()
            return render(request, 'crm/verification_code.html', {'form_new_passwd': form_new_passwd})

    form_email = RestoreAccountForm()

    return render(request, 'crm/restore_account.html', {'form_email': form_email})

def user_management(request):
    pass

def verification_email(email):
    user_by_email = get_or_none(User, email=email)
    if user_by_email:
        return True
    else:
        return False

# replaces block try/except
def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except:
        return None
