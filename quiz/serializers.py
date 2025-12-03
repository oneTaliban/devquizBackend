from rest_framework import serializers

from .models import Participant, QuizSession, Question, ParticipantAnswers

class QuestionSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'difficulty', 'category']

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'username', 'joined_at']

class ParticipantAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipantAnswers
        fields = ['participant', 'question', 'selected_answer', 'is_correct']
