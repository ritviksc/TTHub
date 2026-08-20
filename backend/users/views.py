from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
def login_view(request) -> Response:
    # Get username and password from POST request
    username = request.data["username"]
    password = request.data["password"]


    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None: # No user found
        return Response(
            {"error": "Invalid userame or password"},
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

