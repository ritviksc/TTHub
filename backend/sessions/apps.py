from django.apps import AppConfig


class SessionsConfig(AppConfig):
    name = "sessions"
    # django.contrib.sessions already owns the default "sessions" app label.
    label = "programme_sessions"
