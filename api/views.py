from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from api.decorators import time_logger


class TokenView(APIView):
    """
    Universal token endpoint.

    Methods:
        POST — Obtain an API token (login)
        GET — Check if token is valid (authentication check)
        DELETE — Delete current token (logout)
    """
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        # POST (login) does not require authentication
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    @time_logger
    def post(self, request):
        """
        Obtain an API token by providing username and password.
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Both username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)

    @time_logger
    def get(self, request):
        """
        Checks if the provided token is valid.
        """
        user = request.user
        return Response({
            'status': 'valid',
            'user': user.username
        }, status=status.HTTP_200_OK)

    @time_logger
    def delete(self, request):
        """
        Deletes the token that was used for authentication (logout).
        """
        try:
            request.auth.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AttributeError:
            return Response(
                {'error': 'No token found to delete.'},
                status=status.HTTP_400_BAD_REQUEST
            )
