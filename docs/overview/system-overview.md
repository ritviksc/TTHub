# System overview

Taurite Tū is a web app for running a strength and balance programme for kaumātua: its branches (kapa), staff, participants, classes, attendance, physical assessments, documents and reporting.

```
Group_4/
|---> backend/         Django API, database models, permissions
|---> frontend/        Vue website that staff use
|---> docs/            Setup guides, feature references and conventions
|---> scripts/         Development launcher (dev.sh)
|---> .venv/           Local Python environment (not committed)
|---> .env             Local configuration and credentials (not committed)
```

The main flow of the system:

```
Vue page -> API request   -> Django permissions and validation -> Database
         <- JSON response <-
```

- **Frontend**: Vue 3, Vue Router, Vite and Axios.
- **Backend**: Django and Django REST Framework, with an SQLite database. Settings for Postgres are left commented out in `backend/config/settings.py`.
- **Background work**: Celery runs the AI report jobs, with Redis as the broker. Redis also serves as Django's cache.
- **AI**: an OpenAI-compatible model server explains report statistics and powers the help chatbot (see [llm.md](../backend/llm.md)).

Three roles use the app: kaimahi (instructors), branch managers and super admins. The frontend router hides pages a role can't use, and the backend enforces every permission again.
