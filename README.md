# Group_4

## Backend setup

```powershell
# from repo root, with .venv already created (see docs/backend/venv-setup.md) and activated
cd backend
python manage.py migrate
python manage.py runserver
```

## Create a Django super user

```powershell
python manage.py shell
```

```python
from getpass import getpass
from users.models import UserAccount
UserAccount.objects.create_superuser(
    username="admin@example.com",
    email="admin@example.com",
    password=getpass("Admin password: "),
    role=UserAccount.Role.SUPER_ADMIN,
)
```

## Create a temp user

`role` is required on `UserAccount`, so use the shell instead of `createsuperuser`:

```powershell
python manage.py shell
```
```python
from users.models import UserAccount
UserAccount.objects.create_user(
    username="testuser@example.com",
    email="testuser@example.com",
    password="TestPass123!",
    role=UserAccount.Role.SUPER_ADMIN,
)
exit()
```
