from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or f'Chat {self.id}'}"


class AIRequestLog(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_requests')
    
    prompt = models.TextField()
    model_used = models.CharField(max_length=100)
    response_text = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Request {self.id} by {self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)