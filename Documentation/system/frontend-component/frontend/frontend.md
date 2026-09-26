# Frontend

The frontend is divided into:
```
[router/index.js]: maps URLs to pages and specifies allowed roles.
[apis.js]: defines requests for login, branches, participants, sessions, and attendance.
stores/auth.js: holds the current logged-in user.
views/: contains the pages, mostly grouped by role.
components/: contains reusable navigation and UI components.
assets/: contains shared styling and images.
```

Login uses Django session cookies. The frontend requests /api/auth/me/ to identify the current user, and its router checks their role before opening protected pages. The backend separately enforces access.