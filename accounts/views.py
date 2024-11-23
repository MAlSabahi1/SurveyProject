from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from .forms import UserForm, GroupForm
from django.contrib.auth.decorators import login_required, user_passes_test


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"




def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')  # Redirect to a list of users
    else:
        form = UserForm()
    return render(request, 'registration/create_user.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'registration/edit_user.html', {'form': form, 'user': user})


# views.py
@login_required
@user_passes_test(is_admin)
def group_list(request):
    groups = Group.objects.all()  # جلب جميع المجموعات
    
    if request.method == 'POST':
        # معالجة الطلب وحفظ التحديثات
        for group in groups:
            form = GroupPermissionForm(request.POST, instance=group, prefix=str(group.id))
            if form.is_valid():
                # هنا يمكننا حفظ الصلاحيات كما ترغب. مثلاً تخزينها في قاعدة بيانات
                # أو تعديل الحقول المناسبة بناءً على التطبيق الخاص بك
                pass  # يمكن استبدال هذا بحفظ المعلومات في قاعدة البيانات أو تعديل الحقول
        return redirect('group_permissions')  # إعادة توجيه بعد الحفظ
    forms = [GroupPermissionForm(instance=group, prefix=str(group.id)) for group in groups]  # إنشاء نموذج لكل مجموعة
    print(forms,'1111111111111111111111111111111111')
    return render(request, 'registration/group_permissions.html', {'forms': forms})


@login_required
@user_passes_test(is_admin)
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')  # Redirect to a list of groups
    else:
        form = GroupForm()
    return render(request, 'registration/create_group.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk)  # جلب المجموعة المحددة أو عرض 404 إذا لم تكن موجودة
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)  # استخدام النموذج الحالي لتعديل المجموعة
        if form.is_valid():
            form.save()
            return redirect('group_list')  # إعادة توجيه المستخدم إلى صفحة عرض المجموعات
    else:
        form = GroupForm(instance=group)
    return render(request, 'registration/edit_group.html', {'form': form, 'group': group})

@login_required
@user_passes_test(is_admin)
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)  # جلب المجموعة أو عرض خطأ 404 إذا لم تكن موجودة
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')  # إعادة التوجيه بعد الحذف
    return render(request, 'registration/delete_group.html', {'group': group})

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all()  # Get all users
    return render(request, 'registration/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def group_list(request):
    groups = Group.objects.all()  # Get all groups
    return render(request, 'registration/group_list.html', {'groups': groups})


@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active  # Toggle the active status
    user.save()
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'registration/edit_user.html', {'form': form, 'user': user})
