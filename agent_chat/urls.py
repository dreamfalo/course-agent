from django.urls import path
from agent_chat.views import agent_chat, chat_history, chat_sessions, delete_session

urlpatterns = [
    path("chat/", agent_chat, name="agent_chat"),
    path("history/", chat_history, name="chat_history"),
    path("sessions/", chat_sessions, name="chat_sessions"),
    path("sessions/delete/", delete_session, name="delete_session"),
]