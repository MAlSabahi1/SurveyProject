# forms.py
from django import forms
from django.contrib.auth.models import User, Group, Permission

# forms.py
from django import forms
from django.contrib.auth.models import User, Group, Permission

class GroupPermissionForm(forms.ModelForm):
    can_add = forms.BooleanField(required=False, label='إضافة')
    can_delete = forms.BooleanField(required=False, label='حذف')
    can_edit = forms.BooleanField(required=False, label='تعديل')

    class Meta:
        model = Group
        fields = ['name', 'can_add', 'can_delete', 'can_edit']

class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='المجموعات'
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        label='أذونات المستخدم'
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'groups', 'user_permissions']
        labels = {
            'username': 'اسم المستخدم',
            'password': 'كلمة المرور',
            'email': 'البريد الإلكتروني',
        }
        widgets = {
            'password': forms.PasswordInput(),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_m2m()
        return user


# forms.py
class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all(), required=False)

    class Meta:
        model = Group
        fields = ['name', 'permissions']
