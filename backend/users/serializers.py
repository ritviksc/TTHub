from rest_framework import serializers
from .models import UserAccount, Branch

class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta: 
        model = UserAccount
        fields = ["id", "email", "first_name", "last_name", "role", "branch", "password"]
        read_only_fields = ["id"]
        extra_kwargs = {"branch": {"required": False}}

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        attrs["email"] = email

        if UserAccount.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "An account with this email already exists."})

        requesting_user = self.context["request"].user
        role = attrs.get("role")

        if role == UserAccount.Role.SUPER_ADMIN and requesting_user.role != UserAccount.Role.SUPER_ADMIN:
            raise serializers.ValidationError({"role": "Only a Super Admin can grant the Super Admin role."})

        if requesting_user.role == UserAccount.Role.BRANCH_MANAGER:
            if role != UserAccount.Role.INSTRUCTOR:
                raise serializers.ValidationError({"role": "Branch Managers can only create Instructor accounts."})
            attrs["branch"] = requesting_user.branch

        if role == UserAccount.Role.SUPER_ADMIN:
            attrs["branch"] = None

        if role != UserAccount.Role.SUPER_ADMIN and not attrs.get("branch"):
            raise serializers.ValidationError({"branch": "Branch is required for this role."})

        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = UserAccount(username=validated_data["email"], **validated_data)
        user.set_password(password)
        user.save()
        return user

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "region"]

class StaffListSerializer(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = UserAccount
        fields = ["id", "email", "first_name", "last_name", "role", "branch_name", "is_active"]

    def get_branch_name(self, obj):
        return obj.branch.name if obj.branch else None

class StaffDetailSerializer(serializers.ModelSerializer):
    """
    Serializer used by the shared staff detail page.

    Super Admin:
        - Can edit identity
        - Can edit email
        - Can change role
        - Can change branch

    Branch Manager:
        - Can edit instructor identity/contact details
        - Cannot change role
        - Cannot change branch
    """

    class Meta:
        model = UserAccount

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "branch",
            "is_active",
        ]

        read_only_fields = [
            "id",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if (
            request
            and request.user.role != UserAccount.Role.SUPER_ADMIN
        ):
            self.fields["role"].read_only = True
            self.fields["branch"].read_only = True

    def validate_email(self, value):
        # Login normalizes the credential before matching it against username.
        value = value.strip().lower()
        qs = UserAccount.objects.filter(
            email__iexact=value
        )

        if self.instance:
            qs = qs.exclude(
                pk=self.instance.pk
            )

        if qs.exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate(self, attrs):
        request = self.context["request"]

        role = attrs.get(
            "role",
            self.instance.role
        )

        branch = attrs.get(
            "branch",
            self.instance.branch
        )

        # Promotion also removes the previous branch, matching account creation.
        if role == UserAccount.Role.SUPER_ADMIN:
            attrs["branch"] = None

        # Other staff must have a branch
        elif branch is None:

            raise serializers.ValidationError({
                "branch":
                    "Branch is required for this role."
            })

        # Branch Manager restrictions
        if (
            request.user.role
            == UserAccount.Role.BRANCH_MANAGER
        ):

            if (
                self.instance.role
                != UserAccount.Role.INSTRUCTOR
                or
                self.instance.branch_id
                != request.user.branch_id
            ):
                raise serializers.ValidationError(
                    "You can only edit instructors in your own branch."
                )

        return attrs

    def update(self, instance, validated_data):

        # Username is based on email.
        if "email" in validated_data:
            validated_data["username"] = (
                validated_data["email"]
            )

        return super().update(
            instance,
            validated_data
        )


class BranchListSerializer(serializers.ModelSerializer):
    """A row in the Branch table. participant_count and the manager come from
    annotations/prefetch on the view, so rendering the list stays a fixed
    number of queries however many branches there are."""

    manager_name = serializers.SerializerMethodField()
    participant_count = serializers.IntegerField(read_only=True)
    instructor_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id", "name", "region",
            "manager_name", "instructor_count", "participant_count",
        ]

    def get_manager_name(self, obj):
        # to_attr="managers" on the view already narrowed this to active
        # branch managers, so there is nothing to filter here.
        managers = getattr(obj, "managers", [])
        if not managers:
            return None
        manager = managers[0]
        return manager.get_full_name() or manager.username


def _staff_rows(people):
    """Shared shape for the manager and instructor lists on the branch page."""
    return [
        {
            "id": str(person.id),
            "name": person.get_full_name() or person.username,
            "email": person.email,
        }
        for person in people
    ]


class BranchDetailSerializer(BranchListSerializer):
    """The branch page. Same read-only extras as the table row, but name and
    region are editable here (the view restricts who may write).

    A branch can have more than one manager, so the page gets the full list
    while the table keeps the single manager_name it has room for."""

    managers = serializers.SerializerMethodField()
    instructors = serializers.SerializerMethodField()

    class Meta(BranchListSerializer.Meta):
        fields = BranchListSerializer.Meta.fields + ["managers", "instructors"]
        read_only_fields = ["id"]

    def get_managers(self, obj):
        return _staff_rows(getattr(obj, "managers", []))

    def get_instructors(self, obj):
        return _staff_rows(getattr(obj, "instructors", []))
