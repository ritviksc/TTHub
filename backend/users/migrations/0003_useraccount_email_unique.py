# Generated manually to make staff email addresses a database-level unique credential.

from django.db import migrations, models


def make_email_the_login_credential(apps, schema_editor):
    UserAccount = apps.get_model("users", "UserAccount")
    users = list(UserAccount.objects.all())

    normalized_emails = {}
    for user in users:
        email = (user.email or "").strip().lower()
        if not email:
            raise RuntimeError(
                f"User '{user.username}' has no email address. Add one before applying "
                "the email-login migration."
            )
        if email in normalized_emails:
            raise RuntimeError(
                f"Users '{normalized_emails[email]}' and '{user.username}' share "
                f"the email address '{email}'. Resolve the duplicate before applying "
                "the email-login migration."
            )
        normalized_emails[email] = user.username

    # Avoid a transient unique-username collision if two users' usernames and
    # emails are swapped. The UUID primary key makes each temporary name unique.
    for user in users:
        user.username = f"email-login-migration-{user.pk}"
        user.save(update_fields=["username"])

    for user in users:
        email = (user.email or "").strip().lower()
        user.email = email
        user.username = email
        user.save(update_fields=["email", "username"])


def reverse_email_login_credential(apps, schema_editor):
    # The original usernames cannot be recovered after an email-login upgrade.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_branch_useraccount_branch"),
    ]

    operations = [
        migrations.RunPython(
            make_email_the_login_credential,
            reverse_email_login_credential,
        ),
        migrations.AlterField(
            model_name="useraccount",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
