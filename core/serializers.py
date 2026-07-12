from django.contrib.auth.models import User
from rest_framework import serializers
from .models import AIConversation, AIRequestLog, AIConversation


class UserSerializer(serializers.ModelSerializer):
    snippets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AIConversation.objects.all()
    )

    class Meta:
        model = User
        fields = ["id", "username", "ai_conversations"]


class AIRequestInputSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    model = serializers.CharField(default="default-model", required=False)


class AIRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequestLog
        fields = [
            "id",
            "prompt",
            "model_used",
            "response_text",
            "status",
            "error_message",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "created_at",
        ]


class AIConversationSerializer(serializers.ModelSerializer):
    logs = AIRequestLogSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = ["id", "title", "created_at", "updated_at", "logs"]
