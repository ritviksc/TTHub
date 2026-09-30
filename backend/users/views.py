from collections.abc import Mapping

from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Branch, UserAccount
from .serializers import (

    BranchSerializer,
    BranchDetailSerializer,
    BranchListSerializer,
    StaffCreateSerializer,
    StaffListSerializer,
    StaffDetailSerializer,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from .permissions import IsSuperAdmin, IsBranchManager, IsInstructor
 
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
def login_view(request) -> Response:
    # Staff sign in with their email address. UserAccount.username is retained
    # for Django compatibility and mirrors the normalized email value.
    if not isinstance(request.data, Mapping):
        return Response({"detail": "Provide a JSON object containing email and password."}, status=status.HTTP_400_BAD_REQUEST)
    email = request.data.get("email", "")
    password = request.data.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        return Response({"detail": "Email and password must be strings."}, status=status.HTTP_400_BAD_REQUEST)
    email = email.strip().lower()
 
    user = authenticate(
        request,
        username=email,
        password=password,
    )
 
    if user is None: # No user found
        return Response(
            {"error": "Invalid email or password"},
            status = status.HTTP_401_UNAUTHORIZED,
        )
 
    # Valid user -- login and create session for user
    login(request, user)
 
    return Response(
        {"message": "Login succesful",
         "role": user.role,
        },
        status = status.HTTP_200_OK,
    )
 
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request) -> Response:
    return Response(
        {"detail": "CSRF cookie set"}
        )
 
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request) -> Response:
    logout(request)
    return Response(
        {"detail": "User logged out"}
    )
 
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "branch": {"id": str(user.branch.id), "name": user.branch.name} if user.branch else None,
    })
 
class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
 
class StaffCreateView(generics.CreateAPIView):
    serializer_class = StaffCreateSerializer
    permission_classes = [IsSuperAdmin | IsBranchManager]

def staff_queryset_for(user):
    qs = UserAccount.objects.exclude(id=user.id)
    if user.role == UserAccount.Role.BRANCH_MANAGER:
        if not user.branch_id:
            return qs.none()
        qs = qs.filter(branch=user.branch, role=UserAccount.Role.INSTRUCTOR)
    return qs

class StaffListView(generics.ListAPIView):
    serializer_class = StaffListSerializer
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def get_queryset(self):
        return staff_queryset_for(self.request.user)

class StaffDetailView(
    generics.RetrieveUpdateAPIView
):
    serializer_class = StaffDetailSerializer

    permission_classes = [
        IsSuperAdmin | IsBranchManager
    ]

    def get_queryset(self):
        return staff_queryset_for(
            self.request.user
        )


class StaffDeactivateView(generics.GenericAPIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def post(self, request, pk):
        staff = get_object_or_404(staff_queryset_for(request.user), pk=pk)
        staff.is_active = False
        staff.save()
        return Response({"id": str(staff.id), "is_active": staff.is_active})


ACTIVE_MANAGERS = UserAccount.objects.filter(
    role=UserAccount.Role.BRANCH_MANAGER, is_active=True
)

ACTIVE_INSTRUCTORS = UserAccount.objects.filter(
    role=UserAccount.Role.INSTRUCTOR, is_active=True
)


def branches_for(user):
    """Every branch this user may see, with the columns the table needs.

    A Super Admin works nationally; everyone else is scoped to their own branch,
    the same rule the participant endpoints use.
    """
    qs = Branch.objects.annotate(
        participant_count=Count(
            "participants",
            filter=Q(participants__is_active=True),
            distinct=True,
        ),
        manager_count=Count(
            "staff",
            filter=Q(
                staff__role=UserAccount.Role.BRANCH_MANAGER,
                staff__is_active=True,
            ),
            distinct=True,
        ),
        instructor_count=Count(
            "staff",
            filter=Q(
                staff__role=UserAccount.Role.INSTRUCTOR,
                staff__is_active=True,
            ),
            distinct=True,
        ),
    ).prefetch_related(
        Prefetch("staff", queryset=ACTIVE_MANAGERS, to_attr="managers"),
        Prefetch("staff", queryset=ACTIVE_INSTRUCTORS, to_attr="instructors"),
    )

    if user.role != UserAccount.Role.SUPER_ADMIN:
        qs = qs.filter(pk=user.branch_id)

    return qs


class BranchListCreateView(generics.ListCreateAPIView):
    """The Branch table, and the Add branch action behind it.

    Every signed-in role can read the list; only a Super Admin can add one.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BranchListSerializer
        return BranchSerializer

    def get_queryset(self):
        qs = branches_for(self.request.user)

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(region__icontains=search))

        if self.request.query_params.get("no_manager") == "true":
            qs = qs.filter(manager_count=0)

        return qs


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """One branch: the detail page reads it, a Super Admin edits or deletes it."""

    serializer_class = BranchDetailSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        return branches_for(self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Deleting a branch is refused while anyone still points at it.

        Both UserAccount.branch and Participant.branch are PROTECT, so the
        alternative is a database error. Saying which records are in the way is
        more use than a 500, and it keeps people's records from vanishing with
        the branch they happened to belong to.
        """
        branch = self.get_object()

        blockers = []
        staff_count = branch.staff.count()
        participant_count = branch.participants.count()
        session_count = branch.programme_sessions.count()
        report_count = branch.attendanceanalysisjob_set.count()
        physical_count = branch.assessment_set.count()
        physical_report_count = branch.physicalanalysisjob_set.count()
        if staff_count:
            blockers.append(f"{staff_count} staff account{'s' if staff_count > 1 else ''}")
        if participant_count:
            blockers.append(
                f"{participant_count} participant{'s' if participant_count > 1 else ''}"
            )

        if session_count:
            blockers.append(f"{session_count} programme session(s)")

        if report_count:
            blockers.append(f"{report_count} attendance report job(s)")

        if physical_count:
            blockers.append(f"{physical_count} physical assessment(s)")

        if physical_report_count:
            blockers.append(f"{physical_report_count} physical report job(s)")

        if blockers:
            return Response(
                {
                    "detail": (
                        f"Cannot delete {branch.name}: it still has "
                        + " and ".join(blockers)
                        + ". Move or remove them first."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        branch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BranchStaffView(generics.GenericAPIView):
    """Assign someone to this branch in a given role.

    The role comes from the URL via as_view(role=...), so managers and
    instructors run through exactly the same rules.
    """

    permission_classes = [IsSuperAdmin | IsBranchManager]
    role = None

    def post(self, request, pk):
        # Branch managers may only assign instructors to their own branch
        if request.user.role == UserAccount.Role.BRANCH_MANAGER:
            if str(pk) != str(request.user.branch_id):
                return Response(
                {"detail": "You can only assign instructors to your own branch."},
                status=status.HTTP_403_FORBIDDEN,
            )
            if self.role != UserAccount.Role.INSTRUCTOR:
                return Response(
                    {"detail": "Branch managers may only assign instructors."},
                    status=status.HTTP_403_FORBIDDEN,
            )
        branch = get_object_or_404(Branch, pk=pk)
        if not isinstance(request.data, Mapping):
            return Response({"detail": "Provide an object containing user_id."}, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserAccount.objects.get(pk=user_id)
        except (UserAccount.DoesNotExist, DjangoValidationError, ValueError, TypeError):
            # user_id arrives in the body, so it is not filtered by the URL
            # converter the way pk is. A malformed id is "no such user", not a
            # database error.
            return Response(
                {"detail": "No user account matches that id."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == UserAccount.Role.SUPER_ADMIN:
            return Response(
                {"detail": "A Super Admin works nationally and cannot be assigned to a branch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return Response(
                {"detail": "That account is deactivated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Assigning from this page also sets the role, so this can promote an
        # instructor or step a manager down. The UI reports whichever happened.
        previous_role = user.role
        role_changed = previous_role != self.role
        moved_from = user.branch.name if user.branch and user.branch_id != branch.id else None

        user.role = self.role
        user.branch = branch
        user.save()

        return Response(
            {
                "id": str(user.id),
                "name": user.get_full_name() or user.username,
                "role": user.role,
                "previous_role": previous_role,
                "role_changed": role_changed,
                "moved_from": moved_from,
            }
        )


class BranchStaffDetailView(generics.GenericAPIView):
    """Unassign someone from this branch."""

    permission_classes = [IsSuperAdmin]
    role = None

    def delete(self, request, pk, user_id):
        branch = get_object_or_404(Branch, pk=pk)
        person = get_object_or_404(UserAccount, pk=user_id, branch=branch, role=self.role)

        # Unassigned, not deleted or demoted: the account stays exactly as it
        # was so it can be pointed at another branch.
        person.branch = None
        person.save()

        return Response({"id": str(person.id), "branch": None})
