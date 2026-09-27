# Backend

The backend is divided into four main 'apps':
```
Folder          Responsibility
users/	        Staff accounts, login/logout, roles, and branches
participants/   Participant details, emergency contacts, photos, and consent
sessions/       Programme classes, attendance, and absence reasons
llm/	       AI report-generation/analysing 
```

Rule of thumb is to add a new 'app' for new features that are themselves a subsystem of the whole system in addition to the ones listed above.

# Database relationships

The relationships can be visualised as:

```
Branch
|--> Staff accounts
|--> Participants
|--> Programme sessions
    |--> Attendance records --> Participants
```