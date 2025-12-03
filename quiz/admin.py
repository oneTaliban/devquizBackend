from django.contrib import admin
from .models import Participant, ParticipantAnswers, Question, QuizSession

admin.site.register(Participant)
admin.site.register(ParticipantAnswers)
admin.site.register(QuizSession)
admin.site.register(Question)
