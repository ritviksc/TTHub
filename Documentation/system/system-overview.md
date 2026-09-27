# System Overview 

This directory contains the code for Taurite Tū, an app for managing a strength and balance programme: its branches, staff, participants, classes, attendance, and reporting/analysing features.

```
Group_4/
|---> backend/         Django API, database models, permissions
|---> frontend/        Vue website that staff interact with
|---> docs/            **Important for new developers working on the system**
                       Setup guides, coding conventions, UI mockups
|---> .venv/           Local Python environment
|---> .env             Local configuration and service credentials
|---> llm_test.py      Standalone script for experimenting with the LLM
```
```
The main flow of the system is:  
Vue page -> API request   -> Django permissions and validation -> Database
         <- JSON response <-
```

The frontend uses Vue 3, Vue Router, Vite, and Axios. 
The backend uses Django and Django REST Framework, configured to use Postgres in the final release. 
Redis and Celery are also configured for caching and background work related to the AI integration.
