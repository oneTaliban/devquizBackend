import os
import json

from django.core.management.base import BaseCommand
from django.conf import settings
from quiz.models import Question

class Command(BaseCommand):
    help = 'Populate database with 100+ developer questions from json file'

    def handle(self, *args, **options):
        #Path to the json file
        json_file_path = os.path.join(settings.BASE_DIR, 'dev_questions.json')
        print(json_file_path)

        try: 
            with open(json_file_path, 'r', encoding='utf-8') as file:
                question_data = json.load(file)
            
            created_count = 0
            skipped_count = 0

            for q_data in question_data:
                #checking if question already exists to avoid duplicates
                if not Question.objects.filter(text = q_data['text']).exists():
                    Question.objects.create(
                        text = q_data['text'],
                        options = q_data['options'],
                        correct_answer = q_data['correct_answer'],
                        defficulty = q_data['difficulty'],
                        category = q_data['category'],
                        explanation = q_data.get('explanation', '')
                    )
                    created_count += 1
                    print(f"Populated questions {created_count}")
                else: 
                    skipped_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {created_count} qestions"
                )
            )


        except FileNotFoundError:
            self.stderr.write(f"JSON file not found at the specified location: '{json_file_path}'")
        except json.JSONDecodeError as e:
            self.stderr.write(f"Invalid JSON format : {e}")
        except KeyError as e: 
            self.stderr.write(f"Missing required field in JSON: {e}")
