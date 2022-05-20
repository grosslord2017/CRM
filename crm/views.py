import json
from datetime import date
from .sender import send_mail
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .models import Profile, Task, ArchiveTask, Position, Comment
from django.shortcuts import render, HttpResponseRedirect, HttpResponse, Http404
from .forms import AutorizationForm, UserRegistrationForm, UserEditForm, ProfileFillingForm, TaskCreateForm,\
    CommentCreateForm, DepartmentCreateForm, PositionCreateForm


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
    group = Group.objects.all()
    position = Position.objects.all()
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_filling_form = ProfileFillingForm(request.POST)
        if user_form.is_valid() and user_filling_form.is_valid():
            profile = user_filling_form.cleaned_data
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
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

# пока работает нормлаьно, но возможно надо будет допиливать!!!! и добавить проверку на дату из прошлого
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
    # tasks = Task.objects.filter(executor_id=profile, status_completed=False).all()
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

def choice_position(request):
    department_id = json.loads(request.body).get('depId')
    if department_id:
        positions = Position.objects.filter(department_fk=department_id)
        pos_list = []
        for position in positions:
            pos_l = [position.name, position.id]
            pos_list.append(pos_l)

        return JsonResponse({'pos_l': pos_list})

def choice_profile(request):
    department_id = json.loads(request.body).get('depId')
    task_id = json.loads(request.body).get('taskId')
    positions = Position.objects.filter(department_fk=department_id)
    pos_profile = []

    if task_id:
        task = Task.objects.get(id=task_id)
        for position in positions:
            pos_prof = Profile.objects.filter(~Q(user_id=request.user.id) & ~Q(id=task.task_manager.profile.id),
                                              position=position.id)
            if pos_prof:
                for pos_p in pos_prof:
                    prof = [pos_p.name, pos_p.surname, position.name, pos_p.id]
                    pos_profile.append(prof)
    else:
        for position in positions:
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
        if request.POST.get('department', False):
            try:
                department = Group.objects.get(name=request.POST['department'])
            except:
                Group.objects.create(
                    name=request.POST['department']
                )
                messages.success(request, 'Department create successfully')
                return HttpResponseRedirect('/create_workplace/')
        elif request.POST.get('position', False):
            try:
                position = Position.objects.get(name=request.POST['position'])
            except:
                Position.objects.create(
                    department_fk=Group.objects.get(id=int(request.POST['dep_id'])),
                    name=request.POST['position']
                    )
                messages.success(request, 'Position create successfully')
                return HttpResponseRedirect('/create_workplace/')

    else:
        form_dep = DepartmentCreateForm()
        form_pos = PositionCreateForm()
    return render(request, 'crm/create_workplace.html', {'form_dep': form_dep,
                                                         'form_pos': form_pos,
                                                         'dep': dep})


