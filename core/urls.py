from django.urls import path
from .views import send_ai_request, conversation_history_list, conversation_detail

urlpatterns = [
    path("ai/chat/", send_ai_request, name="ai-chat"),
    path("ai/history/", conversation_history_list, name="ai-history"),
    path(
        "ai/history/<int:conversation_id>/",
        conversation_detail,
        name="ai-conversation-detail",
    ),
]

