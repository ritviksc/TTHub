from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Branch, UserAccount
from .serializers import (
    BranchSerializer,
    KapaListSerializer,
    StaffCreateSerializer,
    StaffListSerializer,
)
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from .permissions import IsSuperAdmin, IsBranchManager, IsInstructor
 
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request) -> Response:
    # Get username and password from POST request
    username = request.data.get("username")
    password = request.data.get("password")
 
    user = authenticate(
        request,
        username=username,
        password=password,
    )
 
    if user is None: # No user found
        return Response(
            {"error": "Invalid username or password"},
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
        qs = qs.filter(branch=user.branch, role=UserAccount.Role.INSTRUCTOR)
    return qs

class StaffListView(generics.ListAPIView):
    serializer_class = StaffListSerializer
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def get_queryset(self):
        return staff_queryset_for(self.request.user)

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


class KapaListCreateView(generics.ListCreateAPIView):
    """The Kapa table, and the Add kapa action behind it.

    Every signed-in role can read the list; only a Super Admin can add one.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return KapaListSerializer
        return BranchSerializer

    def get_queryset(self):
        qs = (
            Branch.objects.annotate(
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
            )
            .prefetch_related(Prefetch("staff", queryset=ACTIVE_MANAGERS, to_attr="managers"))
        )

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(region__icontains=search))

        if self.request.query_params.get("no_manager") == "true":
            qs = qs.filter(manager_count=0)

        return qs
