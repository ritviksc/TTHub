from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Branch
from .serializers import BranchSerializer

from django.contrib.auth import logout

from .permissions import IsSuperAdmin
from .serializers import StaffCreateSerializer

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request) -> Response:
    # if user is already logged in, return
    if request.user.is_authenticated:
        return Response(
            {"authenticated": True,
             "role": request.user.role},
            status=status.HTTP_200_OK,
        )

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
        {"authenticated": True,
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
    return Response({"email": user.email, "role": user.role})

class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

class StaffCreateView(generics.CreateAPIView):
    serializer_class = StaffCreateSerializer
    permission_classes = [IsSuperAdmin]