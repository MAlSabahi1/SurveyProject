from django import template

register = template.Library()

@register.filter
def get_answer_text(answers, question_id):
    """
    Retrieves the text answer for a specific question ID from the list of answers.
    """
    for answer in answers:
        if answer.question.id == question_id:
            return answer.answer_text
    return ""

@register.filter
def get_selected_choices(answers, question_id):
    """
    Retrieves the list of selected choice IDs for a specific question ID from the list of answers.
    """
    selected_choices = []
    for answer in answers:
        if answer.question.id == question_id and answer.choice_selected:
            selected_choices.append(answer.choice_selected.id)
    return selected_choices
