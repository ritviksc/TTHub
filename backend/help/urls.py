from django.urls import path

from .views import ArticleDetailView, ArticleListView, ChatView

urlpatterns = [
    path("articles/", ArticleListView.as_view(), name="help-articles"),
    path("articles/<slug:slug>/", ArticleDetailView.as_view(), name="help-article"),
    path("chat/", ChatView.as_view(), name="help-chat"),
]
