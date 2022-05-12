from django.shortcuts import render, HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth import login, authenticate, logout
from .models import Profile, Task, ArchiveTask, Position, Comment
from django.contrib.auth.decorators import login_required
from .forms import AutorizationForm, UserRegistrationForm, UserEditForm, ProfileFillingForm, TaskCreateForm, CommentCreateForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http.response import JsonResponse
import json
from django.db.models import Q

# Create your views here.

def home_crm(request):
    try:
        profile_active_user = Profile.objects.get(user_id=request.user.id)
        user_hot_task = Task.objects.filter(executor_id=profile_active_user,
                                            status_completed=False).order_by('final_date')[:3]
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
        profile_form = ProfileFillingForm(instance=request.user.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileFillingForm(instance=request.user.profile)
    department = Group.objects.all()

    return render(request, 'crm/edit_profile.html', {'user_form': user_form,
                                                     'profile_form': profile_form,
                                                     'depart': department})

# пока работает нормлаьно, но возможно надо будет допиливать!!!! и добавить проверку на дату из прошлого
@login_required
def task_create(request):
    profile = Profile.objects.filter(~Q(user_id=request.user.id))
    print(profile)
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            date_form = form.cleaned_data
            task = Task.objects.create(
                subject=date_form['subject'],
                final_date=date_form['final_date'],
                description=date_form['description'],
                task_manager_id=request.user.id,
                executor_id=date_form['executor'].id,
            )
            task.save()
            return HttpResponseRedirect('/')
    else:
        form = TaskCreateForm()
    return render(request, 'crm/task_form.html', {'form': form, 'profile': profile})

@login_required
def my_task(request):
    profile = Profile.objects.get(user_id=request.user.id)
    # tasks = Task.objects.filter(executor_id=profile, status_completed=False).all()
    tasks = Task.objects.filter(executor_id=profile).all()

    # подумать как вытащить дату завершения таска и прописать ее на странице my_task

    return render(request, 'crm/my_task.html', {'tasks': tasks})

@login_required
def my_task_inside(request, pk):
    task = Task.objects.get(id=pk)
    comment_form = CommentCreateForm()

    if request.method =='POST':
        # block complete task
        # if check-box selected - task changed status_completed - True, else - do nothing.
        is_completed = request.POST.get('status', False)
        if is_completed:
            task_manager = Profile.objects.get(id=task.executor_id)
            task.status_completed = True
            archive = ArchiveTask.objects.create(
                date_create=task.date_create,
                subject=task.subject,
                task_manager=task.task_manager.profile.surname,
                executor=task_manager.surname,
                description=task.description
            )
            archive.save()
            task.save()
            return HttpResponseRedirect('/my_task/')

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

    # output comments
    comments = Comment.objects.filter(task_fk_id=pk).order_by('date')[::-1]

    return render(request, 'crm/my_task_inside.html', {'task': task,
                                                       'comment_form': comment_form,
                                                       'comments': comments})

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
        # block complete task
        # if check-box selected - task changed status_completed - True, else - do nothing.
        # is_completed = request.POST.get('status', False)
        # if is_completed:
        #     task_manager = Profile.objects.get(id=task.executor_id)
        #     task.status_completed = True
        #     archive = ArchiveTask.objects.create(
        #         date_create=task.date_create,
        #         subject=task.subject,
        #         task_manager=task.task_manager.profile.surname,
        #         executor=task_manager.surname,
        #         description=task.description
        #     )
        #     archive.save()
        #     task.save()
        #     return HttpResponseRedirect('/my_task/')

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
            # return HttpResponseRedirect(f'/my_task/{pk}')

    # output comments
    comments = Comment.objects.filter(task_fk_id=pk).order_by('date')[::-1]

    return render(request, 'crm/my_task_inside.html', {'task': task,
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
        position = Position.objects.filter(department_fk=department_id)
        pos_list = []
        # print(position)
        for p in position:
            pos_l = [p.name, p.id]
            pos_list.append(pos_l)

        return JsonResponse({'pos': pos_list})
