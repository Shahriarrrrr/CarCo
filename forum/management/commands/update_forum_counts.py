from django.core.management.base import BaseCommand
from forum.models import ForumThread, ForumResponse


class Command(BaseCommand):
    help = 'Update forum thread response counts and response vote counts'

    def handle(self, *args, **options):
        self.stdout.write('Updating forum thread response counts...')
        
        # Update all thread response counts
        updated_threads = 0
        for thread in ForumThread.objects.all():
            actual_count = thread.responses.count()
            if thread.responses_count != actual_count:
                thread.responses_count = actual_count
                thread.save(update_fields=['responses_count'])
                updated_threads += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated_threads} thread response counts'))
        
        # Update all response vote counts
        self.stdout.write('Updating response vote counts...')
        updated_responses = 0
        for response in ForumResponse.objects.all():
            helpful_count = response.votes.filter(vote_type='helpful').count()
            unhelpful_count = response.votes.filter(vote_type='unhelpful').count()
            
            if response.helpful_count != helpful_count or response.unhelpful_count != unhelpful_count:
                response.helpful_count = helpful_count
                response.unhelpful_count = unhelpful_count
                response.save(update_fields=['helpful_count', 'unhelpful_count'])
                updated_responses += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated_responses} response vote counts'))
        self.stdout.write(self.style.SUCCESS('All forum counts updated successfully!'))
