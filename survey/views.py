from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .models import *
from .forms import *
import pandas as pd
from django.http import HttpResponse, JsonResponse
import csv
from collections import Counter
from django.db.models import Q
from django.http import HttpResponseRedirect

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_entitys(request):
    if request.method == 'POST':
        form = EntitysForm(request.POST)
        if form.is_valid():
            entity = form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        form = EntitysForm()
    
    entities = Entitys.objects.filter(parent__isnull=True)  # جلب الكيانات الرئيسية فقط
    return render(request, 'survey/create_entitys.html', {'form': form, 'entities': entities})


def show_categories(request,pk):
    entity = get_object_or_404(Entitys, pk=pk)
    staff_surveys = Surveys.objects.filter(category='staff',entities = entity)
    infrastructure_surveys = Surveys.objects.filter(category='infrastructure',entities = entity)
    systems_surveys = Surveys.objects.filter(category='systems',entities = entity)
    return render(request, 'survey/categories.html',{
        'entity': entity,
        'staff_surveys': staff_surveys,
        'infrastructure_surveys': infrastructure_surveys,
        'systems_surveys': systems_surveys,
        })

def show_questions_by_category(request, category, pk):
    questions = Question.objects.filter(category=category, is_active=True)
    entity = get_object_or_404(Entitys, pk=pk)
    return render(request, 'survey/questions_by_category.html', {
        'questions': questions,
        'category': category,
        'entity': entity,  # إرسال الـ entity إلى القالب

    })


@login_required
def submit_survey(request, category, pk):
    if request.method == 'POST':
        survey_name = request.POST.get('survey_name')

        # جلب الكيان المحدد بناءً على المعرّف (pk)
        entity = get_object_or_404(Entitys, id=pk)

        # إنشاء استبيان جديد للمستخدم الحالي
        survey = Surveys.objects.create(category=category, user=request.user, name=survey_name)

        # ربط الاستبيان بالكيان المحدد
        survey.entities.add(entity)

        # معالجة الإجابات القادمة من الطلب
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.split('_')[1]
                question = get_object_or_404(Question, id=question_id)

                # قراءة الملاحظات الخاصة بالسؤال
                note_key = f"note_{question_id}"
                note = request.POST.get(note_key, "").strip()

                if question.question_type in ['text', 'yes_no']:
                    # الإجابة النصية أو نعم/لا يتم حفظها مباشرة
                    Answer.objects.create(
                        survey=survey, 
                        question=question, 
                        answer_text=value, 
                        note=note,  # حفظ الملاحظة
                        entity=entity
                    )
                elif question.question_type in ['multiple_choice', 'radio']:
                    # حفظ كل خيار كمجموعة إجابة منفصلة
                    for choice_id in request.POST.getlist(key):
                        choice = Choice.objects.get(id=choice_id)
                        Answer.objects.create(
                            survey=survey, 
                            question=question, 
                            choice_selected=choice, 
                            note=note,  # حفظ الملاحظة
                            entity=entity
                        )

        # إعادة التوجيه إلى صفحة التصنيفات مع الكيان المحدد
        return redirect('categories', pk=entity.id)

    return HttpResponse("Invalid request", status=400)




@login_required
def delete_survey(request, survey_id, entity_id):
    # جلب الاستبيان بناءً على المعرّف
    survey = get_object_or_404(Surveys, id=survey_id, entities__id=entity_id)

    # حذف الاستبيان
    survey.delete()

    # إظهار رسالة نجاح
    messages.success(request, "تم حذف الاستبيان بنجاح.")

    # إعادة التوجيه إلى صفحة عرض التصنيفات
    return redirect('categories', pk=entity_id)


def show_survey(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    answers = Answer.objects.filter(survey=survey)

    # تجميع الإجابات حسب السؤال
    questions_with_answers = {}
    for answer in answers:
        if answer.question not in questions_with_answers:
            questions_with_answers[answer.question] = []
        if answer.answer_text:
            questions_with_answers[answer.question].append(answer.answer_text)
        elif answer.choice_selected:
            questions_with_answers[answer.question].append(answer.choice_selected.text)

    return render(request, 'survey/view_survey.html', {
        'survey': survey,
        'questions_with_answers': questions_with_answers
    })



def is_admin(user):
    return user.is_authenticated and user.is_staff


def filter_questions(keywords=None, question_types=None):
    query = Q()

    if keywords:
        keyword_query = Q()
        for keyword in keywords:
            keyword_query |= Q(text__icontains=keyword)
        query &= keyword_query
    
    if question_types:
        query &= Q(question_type__in=question_types)

    return Question.objects.filter(query)







@login_required
def entity_sector_selection(request):
    entities = Entity.objects.all()
    sectors = []  # Initialize an empty list for sectors

    selected_entity_id = request.POST.get("entity")
    selected_sector_id = request.POST.get("sector")

    # Retrieve sectors only if an entity is selected
    if selected_entity_id:
        sectors = Sector.objects.filter(entity_id=selected_entity_id)

    surveys = None  # Set surveys to None initially

    if request.method == "POST":
        if selected_sector_id:
            # Fetch surveys for the selected sector
            surveys = Surveys.objects.filter(sector_id=selected_sector_id)
        elif selected_entity_id:
            # Fetch surveys for the selected entity that aren't linked to a sector
            surveys = Surveys.objects.filter(entity_id=selected_entity_id, sector__isnull=True)

    return render(request, 'survey/entity_sector_selection.html', {
        'entities': entities,
        'sectors': sectors,
        'surveys': surveys,
        'selected_entity_id': selected_entity_id,
        'selected_sector_id': selected_sector_id,
    })


@login_required
@user_passes_test(is_admin)
def add_question(request):
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)

        if question_form.is_valid():
            question = question_form.save(commit=False)
            # تأكد من حذف أو تعديل السطر التالي حسب ما إذا كنت تحتاج تعيين استبيان محدد للسؤال
            question.save()
            
            # حفظ الاختيارات إذا كان نوع السؤال "اختيار متعدد" أو "راديو"
            if question.question_type in ['multiple_choice', 'radio']:
                choices = request.POST.getlist('choices[]')
                for choice_text in choices:
                    if choice_text.strip():
                        Choice.objects.create(question=question, text=choice_text)
            
            # إرسال رد JSON مع رسالة النجاح
            return JsonResponse({'success': True, 'message': 'تم إضافة السؤال بنجاح!'})
        else:
            # إرسال رد JSON مع رسالة الخطأ
            return JsonResponse({'success': False, 'message': 'حدث خطأ أثناء إضافة السؤال. يرجى التحقق من البيانات وإعادة المحاولة.'})

    else:
        question_form = QuestionForm()

    return render(request, 'survey/add_question.html', {
        'question_form': question_form,
    })



@login_required
@user_passes_test(is_admin)
def get_questions(request):
    return render(request, 'survey/question_category.html')


@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_list(request):
    surveys = Surveys.objects.all()
    return render(request, 'survey/survey_list.html', {'surveys': surveys})

def thank_you(request):
    return render(request, 'survey/thank_you.html')

@login_required
@user_passes_test(is_admin)
def view_survey_answers(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    entity_responses = SurveyEntityResponse.objects.filter(survey=survey)
    entity_answers = {}

    for response in entity_responses:
        entity_id = response.entity.id
        if entity_id not in entity_answers:
            entity_answers[entity_id] = {
                'entity': response.entity,
                'answers': response.answers,
                'sectors': {}
            }
        if response.sector:
            entity_answers[entity_id]['sectors'][response.sector.id] = {
                'sector': response.sector,
                'answers': response.answers
            }

    if request.method == 'POST':
        # Save the answers
        for entity_id, entity_data in entity_answers.items():
            entity_answers_data = {}
            for question in survey.questions.all():
                answer_key = f"entity_{entity_id}_question_{question.id}"
                text_answer = request.POST.get(answer_key, "")
                entity_answers_data[question.text] = {'text_answer': text_answer}
            SurveyEntityResponse.objects.update_or_create(
                survey=survey,
                entity=entity_data['entity'],
                sector=None,
                user=request.user,
                defaults={'answers': entity_answers_data}
            )

        # For sectors
        for entity_id, entity_data in entity_answers.items():
            for sector_id, sector_data in entity_data['sectors'].items():
                sector_answers_data = {}
                for question in survey.questions.all():
                    answer_key = f"sector_{sector_id}_question_{question.id}"
                    text_answer = request.POST.get(answer_key, "")
                    sector_answers_data[question.text] = {'text_answer': text_answer}
                SurveyEntityResponse.objects.update_or_create(
                    survey=survey,
                    entity=entity_data['entity'],
                    sector=sector_data['sector'],
                    user=request.user,
                    defaults={'answers': sector_answers_data}
                )

        messages.success(request, "Answers updated successfully.")
        return redirect('view_survey_answers', survey_id=survey.id)

    return render(request, 'survey/view_survey_answers.html', {
        'survey': survey,
        'entity_answers': entity_answers,
    })
@login_required
@user_passes_test(is_admin)
def choose_survey_for_answers(request):
    surveys = Surveys.objects.all()
    return render(request, 'survey/choose_survey_for_answers.html', {'surveys': surveys})



# @login_required
# @user_passes_test(is_admin)
# def survey_report(request, survey_id):
#     survey = get_object_or_404(Surveys, id=survey_id)
#     answers_data = survey.json_answers  # Get the JSON answers data

#     # Convert JSON answers to DataFrame for analysis
#     df = pd.DataFrame([answers_data])

#     # Generate basic summary statistics
#     report_data = {}
#     for question, responses in answers_data.items():
#         if 'choices' in responses:  # Multiple choice question
#             choices_df = pd.Series(responses['choices']).value_counts()
#             report_data[question] = choices_df.to_dict()
#         elif 'yes_no_answer' in responses:  # Yes/No question
#             report_data[question] = {
#                 'Yes': (responses['yes_no_answer'] == 'yes'),
#                 'No': (responses['yes_no_answer'] == 'no')
#             }
#         else:  # Text responses
#             report_data[question] = responses['text_answer']

#     # Pass data to the template
#     return render(request, 'survey/survey_report.html', {
#         'survey': survey,
#         'report_data': report_data
#     })

@login_required
@user_passes_test(is_admin)
def choose_survey_for_report(request):
    surveys = Surveys.objects.all()
    return render(request, 'survey/choose_survey_for_report.html', {'surveys': surveys})


# @login_required
# @user_passes_test(lambda u: u.is_staff)
# def delete_survey(request, survey_id):
#     survey = get_object_or_404(Surveys, id=survey_id)
#     survey.delete()
#     return redirect('survey_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_report(request, survey_id=None):
    # Fetch all surveys to populate the dropdown
    surveys = Surveys.objects.all()

    # If a survey_id is provided, fetch that specific survey
    selected_survey = None
    if survey_id:
        selected_survey = get_object_or_404(Surveys, id=survey_id)

    return render(request, 'survey/survey_report.html', {
        'surveys': surveys,
        'selected_survey': selected_survey,
    })



# Utility function to check admin status
def is_admin(user):
    return user.is_authenticated and user.is_staff

# 1. Surveys Summary Report
@login_required
@user_passes_test(is_admin)
def survey_summary_report(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    response_data = survey.json_answers
    total_responses = len(response_data)
    question_types = Question.objects.filter(survey=survey).values('question_type').count()

    return render(request, 'survey/summary_report.html', {
        'survey': survey,
        'total_responses': total_responses,
        'question_types': question_types,
    })

# 2. Question-Level Analysis
@login_required
@user_passes_test(is_admin)
def question_analysis_report(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    questions = survey.questions.all()
    
    # Assuming survey.json_answers is structured correctly as a dictionary with questions as keys
    answers_by_question = {
        question.text: survey.json_answers.get(question.text, "لا توجد إجابات") 
        for question in questions
    }

    return render(request, 'survey/question_analysis_report.html', {
        'survey': survey,
        'questions': questions,
        'answers_by_question': answers_by_question,
    })

# 3. Demographic Breakdown
@login_required
@user_passes_test(is_admin)
def demographic_report(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    response_data = pd.DataFrame(survey.json_answers)
    age_breakdown = response_data['age'].value_counts().to_dict() if 'age' in response_data.columns else {}

    return render(request, 'survey/demographic_report.html', {
        'survey': survey,
        'age_breakdown': age_breakdown,
    })

# 4. Trends Over Time
@login_required
@user_passes_test(is_admin)
def time_trend_report(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    response_data = pd.DataFrame(survey.json_answers)
    
    if 'response_date' in response_data.columns:
        response_data['response_date'] = pd.to_datetime(response_data['response_date'])
        trend_over_time = response_data.groupby(response_data['response_date'].dt.date).size().to_dict()
    else:
        trend_over_time = {}

    return render(request, 'survey/time_trend_report.html', {
        'survey': survey,
        'trend_over_time': trend_over_time,
    })

# 5. Completion Analysis

@login_required
@user_passes_test(is_admin)
def completion_analysis(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    
    # Access the JSON data for this survey's answers
    response_data = survey.json_answers

    # Define total_responses as the number of answered questions (non-empty responses)
    total_responses = sum(1 for answer in response_data.values() if any(answer.values()))

    # Assume a response is complete if all required questions have non-empty answers
    questions = survey.questions.all()
    completed_responses = 1 if all(response_data.get(q.text) for q in questions) else 0

    # Calculate completion rate
    completion_rate = (completed_responses / len(questions)) * 100 if questions else 0

    return render(request, 'survey/completion_analysis.html', {
        'survey': survey,
        'total_responses': total_responses,  # This now represents answered questions
        'completion_rate': completion_rate,
    })


# 6. Satisfaction and Feedback Analysis
@login_required
@user_passes_test(is_admin)
def satisfaction_report(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    response_data = survey.json_answers
    satisfaction_scores = [resp['satisfaction'] for resp in response_data if 'satisfaction' in resp]
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

    return render(request, 'survey/satisfaction_report.html', {
        'survey': survey,
        'avg_satisfaction': avg_satisfaction,
    })

# 7. Export Responses as CSV
@login_required
@user_passes_test(lambda u: u.is_staff)
def export_survey_data(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    response_data = survey.json_answers

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{survey.title}_responses.csv"'
    writer = csv.writer(response)

    # Check if json_answers is a dictionary with question-answer pairs
    if isinstance(response_data, dict):
        # Write header
        writer.writerow(['Question', 'Answer'])

        # Write question-answer pairs
        for question, answer in response_data.items():
            if isinstance(answer, dict):
                # Handle different answer types within the dictionary
                if 'choices' in answer:
                    writer.writerow([question, ', '.join(answer['choices'])])
                elif 'text_answer' in answer:
                    writer.writerow([question, answer['text_answer']])
                elif 'yes_no_answer' in answer:
                    writer.writerow([question, answer['yes_no_answer']])
            else:
                writer.writerow([question, answer])
    else:
        # Handle cases where response_data is not in the expected format
        writer.writerow(['Error'])
        writer.writerow(['Unexpected data format in json_answers'])

    return response


@login_required
@user_passes_test(lambda u: u.is_staff)
def dynamic_report(request):
    surveys = Surveys.objects.all()
    keyword = None
    report_data = []  # Store question-by-question analysis here

    # Process the filter form
    if request.method == "GET":
        form = ReportFilterForm(request.GET)
        if form.is_valid():
            keyword = form.cleaned_data['keyword'].lower()

    # Iterate through surveys to analyze answers
    for survey in surveys:
        for question, answer_data in survey.json_answers.items():
            # Filter questions based on the keyword
            if keyword and keyword not in question.lower():
                continue

            question_analysis = {
                'question_text': question,
                'question_type': None,
                'yes_count': 0,
                'no_count': 0,
                'most_common_choices': [],
                'choices_usage': {},
                'text_responses': []
            }

            # Determine the type of question and process responses
            for question_obj in survey.questions.filter(text=question):
                question_analysis['question_type'] = question_obj.question_type

                if question_obj.question_type == 'yes_no':
                    if answer_data.get("yes_no_answer") == "yes":
                        question_analysis['yes_count'] += 1
                    elif answer_data.get("yes_no_answer") == "no":
                        question_analysis['no_count'] += 1

                elif question_obj.question_type == 'multiple_choice' and 'choices' in answer_data:
                    choices_counter = Counter(answer_data['choices'])
                    question_analysis['choices_usage'] = dict(choices_counter)  # Ensure choices_usage is always a dictionary
                    question_analysis['most_common_choices'] = choices_counter.most_common()

                elif question_obj.question_type == 'text' and 'text_answer' in answer_data:
                    question_analysis['text_responses'].append(answer_data['text_answer'])

            report_data.append(question_analysis)

    context = {
        'form': form,
        'surveys': surveys,
        'keyword': keyword,
        'report_data': report_data,
    }

    return render(request, 'survey/dynamic_report.html', context)



@login_required
def survey_summary(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    survey_response, created = SurveyResponse.objects.get_or_create(survey=survey, user=request.user)

    if request.method == 'POST':
        summary_form = SurveySummaryForm(request.POST, instance=survey_response)
        
        question_forms = [
            QuestionNoteForm(request.POST, prefix=str(q.id), instance=QuestionResponse.objects.get_or_create(response=survey_response, question=q)[0])
            for q in survey.questions.all()
        ]

        if summary_form.is_valid() and all(form.is_valid() for form in question_forms):
            summary_form.save()
            for form in question_forms:
                form.save()
            return redirect('survey_list')  # Redirect to a survey list or confirmation page

    else:
        summary_form = SurveySummaryForm(instance=survey_response)
        question_forms = [
            QuestionNoteForm(prefix=str(q.id), instance=QuestionResponse.objects.get_or_create(response=survey_response, question=q)[0])
            for q in survey.questions.all()
        ]

    context = {
        'survey': survey,
        'summary_form': summary_form,
        'question_forms': question_forms,
    }
    return render(request, 'survey/survey_summary.html', context)


# @login_required
# @user_passes_test(lambda u: u.is_staff)
# def create_entity(request):
#     if request.method == 'POST':
#         form = EntityForm(request.POST)
#         if form.is_valid():
#             entity = form.save()
#             # استجابة JSON عند النجاح
#             return JsonResponse({'success': True})
#         else:
#             # استجابة JSON عند وجود خطأ في النموذج
#             return JsonResponse({'success': False, 'errors': form.errors}, status=400)

#     else:
#         form = EntityForm()
#     return render(request, 'entity/create_entity.html', {'form': form})


# @login_required
# def entity_list(request):
#     entities = Entity.objects.all()  # Retrieve all entities
#     return render(request, 'entity/entity_list.html', {'entities': entities})  # Render a template for displaying entities




@login_required
@user_passes_test(lambda u: u.is_staff)
def create_sector(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # استلام البيانات من الطلب
        sector_name = request.POST.get('sector_name')
        entity_id = request.POST.get('entity_id')
        print(sector_name)
        print(entity_id)
        # التحقق من وجود الكيان
        try:
            entity = Entitys.objects.get(id=entity_id)
        except Entitys.DoesNotExist:
            return JsonResponse({'error': 'Entity not found'}, status=404)
        
        # إنشاء قطاع جديد
        sector = Entitys.objects.create(name=sector_name, parent=entity)
        
        # إرجاع الاستجابة بعد إنشاء القطاع بنجاح
        return JsonResponse({'success': True, 'sector_name': sector.name})
    
    # إذا لم يكن الطلب من نوع POST أو غير AJAX
    return JsonResponse({'error': 'Invalid request'}, status=400)





def get_sectors(request):
    entity_id = request.GET.get('entity_id')
    sectors = Sector.objects.filter(entity_id=entity_id).values('id', 'name')
    return JsonResponse({'sectors': list(sectors)})


@login_required
def home(request):
    # entities = Entitys.objects.prefetch_related('sectors', 'surveys').all()
    entities = Entitys.objects.all()
    return render(request, 'home.html', {'entities': entities})


# views.py
@login_required
@user_passes_test(lambda u: u.is_staff)
def link_survey_to_entity_sector(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    
    if request.method == 'POST':
        form = LinkSurveyForm(request.POST, instance=survey)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.entities.set(form.cleaned_data['entities'])  # Link multiple entities
            survey.sectors.set(form.cleaned_data['sectors'])    # Link multiple sectors
            survey.save()
            return redirect('home')  # Redirect to home or another relevant page
    else:
        form = LinkSurveyForm(instance=survey)
    
    return render(request, 'survey/link_survey_to_entity_sector.html', {'form': form, 'survey': survey})


@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_link_list(request):
    surveys = Surveys.objects.all()  # Fetch all surveys
    return render(request, 'survey/survey_link_list.html', {'surveys': surveys})



# @login_required
# @user_passes_test(lambda u: u.is_staff)
# def delete_survey(request, survey_id):
#     survey = get_object_or_404(Surveys, id=survey_id)
#     linked_entities = survey.entities.exists()
#     # linked_sectors = survey.sectors.exists()
    
#     if request.method == "POST":
#         # If linked, show a warning and confirm deletion
#         if linked_entities or linked_sectors:
#             messages.warning(
#                 request, 
#                 f"Surveys '{survey.title}' is connected to entities or sectors. "
#                 "Are you sure you want to delete it?"
#             )
        
#         # If confirmed, delete the survey
#         survey.delete()
#         messages.success(request, f"Surveys '{survey.title}' deleted successfully.")
#         return redirect('survey_list_all')

#     return render(request, 'survey/confirm_delete.html', {
#         'survey': survey,
#         'linked_entities': linked_entities,
#         'linked_sectors': linked_sectors,
#     })


# # views.py

# @login_required
# @user_passes_test(lambda u: u.is_staff)
# def edit_survey(request, survey_id):
#     survey = get_object_or_404(Surveys, id=survey_id)

#     if request.method == 'POST':
#         form = SurveyForm(request.POST, instance=survey)
#         if form.is_valid():
#             form.save()
#             messages.success(request, f"Surveys '{survey.title}' updated successfully.")
#             return redirect('survey_list_all')
#     else:
#         form = SurveyForm(instance=survey)

#     return render(request, 'survey/edit_survey.html', {'form': form, 'survey': survey})



@login_required
@user_passes_test(lambda u: u.is_staff)
def update_survey_answers(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)

    if request.method == 'POST':
        answers_data = request.POST.getlist('answers')
        notes_data = request.POST.getlist('notes')

        for response in SurveyEntityResponse.objects.filter(survey=survey):
            entity_answers = answers_data.get(str(response.entity.id), {})
            response.answers.update(entity_answers)
            response.save()

        messages.success(request, "تم تحديث الإجابات بنجاح.")
        return redirect('view_survey_answers', survey_id=survey_id)

    return redirect('view_survey_answers', survey_id=survey_id)


def entity_report(request):
    # Filter questions to include only the desired types
    allowed_types = ['yes_no', 'multiple_choice', 'radio']
    questions = Question.objects.filter(question_type__in=allowed_types)

    selected_question = request.GET.get('question')
    selected_choice = request.GET.get('choice')
    # print()
    entities = []

    if selected_question and selected_choice:
        question = get_object_or_404(Question, id=selected_question)

        if question.question_type == 'yes_no':
            # Handle Yes/No type
            entities = Answer.objects.filter(question=question, answer_text=selected_choice).select_related('entity')
        else:
            # Handle multiple_choice or radio types
            choice = get_object_or_404(Choice, id=selected_choice)
            entities = Answer.objects.filter(question=question, choice_selected=choice).select_related('entity')

    context = {
        'questions': questions,
        'selected_question': selected_question,
        'selected_choice': selected_choice,
        'entities': [answer.entity for answer in entities],
    }
    return render(request, 'survey/entity_report.html', context)

    
def question_report(request):
    if request.method == "GET":
        questions = Question.objects.all()
        return render(request, 'survey/question_report.html', {'questions': questions})
    
    if request.method == "POST":  # AJAX طلب
        question_id = request.POST.get('question_id')
        question = get_object_or_404(Question, id=question_id)
        answers = Answer.objects.filter(question=question).select_related('entity', 'choice_selected')

        # تجهيز البيانات لإرسالها كـ JSON
        data = {
            'question': question.text,
            'answers': [
                {
                    'answer': answer.choice_selected.text if answer.choice_selected else answer.answer_text or "لا توجد إجابة",
                    'entity': answer.entity.name,
                    'note': answer.note or "-"
                }
                for answer in answers
            ]
        }
        return JsonResponse(data)


def answer_report(request):
    if request.method == "GET":
        # جلب الأسئلة من الأنواع المحددة فقط
        questions = Question.objects.filter(question_type__in=["yes_no", "multiple_choice", "radio"])
        return render(request, 'survey/answer_report.html', {'questions': questions})
    
    if request.method == "POST":  # عند اختيار إجابة معينة
        question_id = request.POST.get('question_id')
        answer_value = request.POST.get('answer_value')
        
        question = get_object_or_404(Question, id=question_id)

        # تصفية الإجابات بناءً على السؤال والإجابة
        if question.question_type == "yes_no":
            answers = Answer.objects.filter(question=question, answer_text=answer_value).select_related('entity')
        else:  # multiple_choice أو radio
            answers = Answer.objects.filter(question=question, choice_selected__text=answer_value).select_related('entity')

        # تجهيز البيانات لإرسالها
        data = {
            'entities': [
                {
                    'name': answer.entity.name,
                    'survey_id': answer.survey.id,  # إذا أردت عرض معرف الاستبيان
                    'note': answer.note or "-"
                }
                for answer in answers
            ]
        }
        return JsonResponse(data)

def get_choices(request, question_id):
    question = get_object_or_404(Question, id=question_id, question_type__in=["multiple_choice", "radio"])
    choices = Choice.objects.filter(question=question)

    return JsonResponse({
        'choices': [{'id': choice.id, 'text': choice.text} for choice in choices]
    })

def edit_survey(request, survey_id):
    survey = get_object_or_404(Surveys, id=survey_id)
    answers = Answer.objects.filter(survey=survey).select_related('question', 'choice_selected')
    questions = Question.objects.filter(category=survey.category, is_active=True)
    entity = survey.entities.first() 

    # عند إرسال النموذج
    if request.method == 'POST':
        for question in questions:
            question_key = f"question_{question.id}"

            # إذا كان السؤال من نوع نص
            if question.question_type == 'text':
                answer_text = request.POST.get(question_key, "")
                Answer.objects.update_or_create(
                    survey=survey,
                    question=question,
                    defaults={"answer_text": answer_text},
                    entity=entity

                )

            # إذا كان السؤال من نوع نعم/لا
            elif question.question_type == 'yes_no':
                answer_text = request.POST.get(question_key, None)
                if answer_text:
                    Answer.objects.update_or_create(
                        survey=survey,
                        question=question,
                        defaults={"answer_text": answer_text},
                        entity=entity
                    )

            # إذا كان السؤال متعدد الخيارات أو مجموعة خيارات
            elif question.question_type in ['multiple_choice', 'radio']:
                selected_choices = request.POST.getlist(question_key)
                Answer.objects.filter(survey=survey, question=question).delete()  # حذف الإجابات القديمة
                for choice_id in selected_choices:
                    choice = Choice.objects.get(id=choice_id)
                    Answer.objects.create(
                        survey=survey,
                        question=question,
                        choice_selected=choice,
                        entity=entity
                    )

        # إعادة توجيه المستخدم بعد الحفظ
        return redirect('categories', pk=entity.id)

    return render(request, 'survey/edit_survey.html', {
        'survey': survey,
        'questions': questions,
        'answers': answers,
    })