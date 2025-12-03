import json
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import QuizSession, ParticipantAnswers, Participant, Question

class QuizConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'quiz_{self.session_id}'

        #create or get session
        self.session = await self.get_or_create_session()

        #Create participant
        self.participant = await self.create_participant()

        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )

        await self.accept()

        #Send welcome message with participant id
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to quiz session',
            'participant_id': str(self.participant.id),
            'session_id': str(self.session_id)
        }))

        #Send first Question
        await self.send_next_question()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'answer_submitted':
            await self.handle_answer_submission(data)
        elif message_type == 'request_next_question':
            await self.send_next_question()

    async def handle_answer_submission(self, data):
        question_id = data.get('question_id')
        selected_answer = data.get('selected_answer')
        print(data)
        #save answer and check correctness
        result = await self.save_answer(question_id, selected_answer)

        #send result back to the user 
        await self.send(text_data=json.dumps({
            'type': 'answer_results',
            'is_correct': result['is_correct'],
            'correct_answer': result['correct_answer'],
            'explanation': result['explanation']
        }))

        #Update progress to all users
        await self.broadcast_progress()

    async def broadcast_progress(self):
        progress = await self.get_session_progress()
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'progress_update',
                'progress': progress
            }
        )

    async def progress_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'progress': event['progress']
        }))

    async def send_next_question(self):
        question = await self.get_random_question()
        if question: 
            await self.send(text_data=json.dumps({
                'type': 'next_question',
                'question': {
                    'id': str(question.id),
                    'text': question.text,
                    'options': question.options,
                    'difficulty': question.defficulty,
                    'category': question.category
                }
            }))

    @database_sync_to_async
    def get_or_create_session(self):
        session, created = QuizSession.objects.get_or_create(id=self.session_id)
        return session

    @database_sync_to_async
    def create_participant(self):
        return Participant.objects.create(session=self.session)

    @database_sync_to_async
    def get_random_question(self):
        return Question.objects.order_by('?').first()

    @database_sync_to_async
    def save_answer(self, question_id, selected_answer):
        question = Question.objects.get(id=question_id)
        is_correct = selected_answer == question.correct_answer
        print("is correct : ",is_correct)
        print(selected_answer)

        ParticipantAnswers.objects.create(
            participant = self.participant,
            question = question,
            selected_answer= selected_answer,
            is_correct = is_correct
        )

        return {
            'is_correct': is_correct,
            'correct_answer':question.correct_answer,
            'explanation': question.explanation
        }

    @database_sync_to_async
    def get_session_progress(self):
        participants = Participant.objects.filter(session=self.session)
        progress_data = {}

        for participant in participants:
            answers = ParticipantAnswers.objects.filter(participant=participant)
            total = answers.count()
            correct = answers.filter(is_correct=True).count()

            progress_data[str(participant.id)] = {
                'total_answered': total,
                'correct_answers': correct,
                'accuracy': round((correct / total * 100) if total > 0 else 0, 2)
            }

        return progress_data