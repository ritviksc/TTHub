from django.urls import path
from .views import AssessmentListView, AssessmentDetailView, ExerciseGroupView, CompleteAssessmentView

urlpatterns = [
    path("participants/<uuid:participant_id>/", AssessmentListView.as_view()),
    path("<uuid:pk>/", AssessmentDetailView.as_view()),
    path("<uuid:pk>/results/<str:group>/", ExerciseGroupView.as_view()),
    path("<uuid:pk>/complete/", CompleteAssessmentView.as_view()),
]
