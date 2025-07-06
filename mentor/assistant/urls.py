from django.urls import path

from .views import (
    FollowUpQuestionView,
    SessionManagementView,
    TaskStatusView,
    TextAnalysisView,
    UserRegistrationView,
)

urlpatterns = [
    path("analysis/", TextAnalysisView.as_view()),
    path("analysis/<str:session_id>/", SessionManagementView.as_view()),
    path("question/", FollowUpQuestionView.as_view()),
    path("task/<str:task_id>/", TaskStatusView.as_view()),
    path("register/", UserRegistrationView.as_view()),
]
