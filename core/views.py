import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import AIConversation, AIRequestLog
from .serializers import AIRequestInputSerializer, AIConversationSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_ai_request(request):
    """
    Accepts a prompt, calls the external AI API, logs the request, and returns the response.
    """
    serializer = AIRequestInputSerializer(data=request.data)
    if not serializer.is_valid():
        print("request data is not valid")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    prompt = validated_data["prompt"]
    model_name = validated_data.get("model", "default-model")
    conversation_id = validated_data.get("conversation_id")

    # 1. Manage or create conversation context
    if conversation_id:
        try:
            conversation = AIConversation.objects.get(
                id=conversation_id, user=request.user
            )
        except AIConversation.DoesNotExist:
            return Response(
                {"error": "Conversation context not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
    else:
        conversation = AIConversation.objects.create(
            user=request.user, title=prompt[:30] + "..." if len(prompt) > 30 else prompt
        )

    log_entry = AIRequestLog.objects.create(
        user=request.user,
        conversation=conversation,
        prompt=prompt,
        model_used=model_name,
        status="PENDING",
    )

    api_url = settings.API_URL
    api_key = settings.API_KEY

    print(f"api_url={api_url}, api_key={api_key}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {"model": model_name, "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            response_data = response.json()

            # Extract choices safely
            choices = response_data.get("choices", [])
            if choices:
                ai_response = choices[0].get("message", {}).get("content", "")
            else:
                ai_response = ""

            # Extract tokens usage safely
            usage = response_data.get("usage", {})
            log_entry.prompt_tokens = usage.get("prompt_tokens", 0)
            log_entry.completion_tokens = usage.get("completion_tokens", 0)

            log_entry.response_text = ai_response
            log_entry.status = "SUCCESS"
            log_entry.save()

            # Update conversation updated timestamp
            conversation.save()

            return Response(
                {
                    "conversation_id": conversation.id,
                    "response": ai_response,
                    "log_id": log_entry.id,
                },
                status=status.HTTP_200_OK,
            )

        else:
            log_entry.status = "FAILED"
            log_entry.error_message = (
                f"API Error: {response.status_code} - {response.text}"
            )
            log_entry.save()
            return Response(
                {"error": "External AI service returned an error."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    except requests.exceptions.RequestException as e:
        log_entry.status = "FAILED"
        log_entry.error_message = str(e)
        log_entry.save()
        return Response(
            {"error": "Failed to connect to AI service."},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_history_list(request):
    """
    Retrieves all past conversations alongside their message logs for the authenticated user.
    """
    conversations = AIConversation.objects.filter(user=request.user).prefetch_related(
        "logs"
    )
    serializer = AIConversationSerializer(conversations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Add this below your existing views in views.py


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """
    Retrieves all details for a specific conversation, including its full message history.
    Ensures the user can only access their own conversations.
    """
    try:
        conversation = AIConversation.objects.prefetch_related("logs").get(
            id=conversation_id
        )
    except AIConversation.DoesNotExist:
        return Response(
            {
                "error": "Conversation not found or you do not have permission to view it."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = AIConversationSerializer(conversation)

    return Response(serializer.data, status=status.HTTP_200_OK)
