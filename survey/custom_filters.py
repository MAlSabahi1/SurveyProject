
from django import template

register = template.Library()

@register.filter
def get_answer_text(answers, question_id):
    """Retrieve the text answer for a specific question."""
    for answer in answers:
        if answer.question.id == question_id:
            return answer.answer_text
    return ""

@register.filter
def get_choice_selected(answers, question_id):
    """Retrieve the selected choice ID for a specific question."""
    for answer in answers:
        if answer.question.id == question_id and answer.choice_selected:
            return answer.choice_selected.id
    return None
