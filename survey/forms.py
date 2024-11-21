from django import forms
from .models import *



class EntitysForm(forms.ModelForm):
    class Meta:
        model = Entitys
        fields = '__all__'  # الحقول التي ستظهر في النموذج
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),  # تخصيص واجهة المستخدم للحقل
            'parent': forms.Select(attrs={'class': 'form-control'}),  # تخصيص واجهة المستخدم للحقل
        }
        labels = {
            'name': 'اسم الكيان',
            'description': 'الوصف',
            'parent': 'القطاع الرئيسي',  # إذا كان الكيان هو قطاع فرعي
        }




class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
    

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text']


