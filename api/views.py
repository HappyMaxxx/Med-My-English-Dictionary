import requests

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from api.decorators import time_logger
from api.serializers import WordSerializer
from dictionary.models import Word

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

class WordListCreateView(APIView):
    """
    POST — Add a new word to the dictionary
    GET — Get a list of words for the current user
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @time_logger
    def get(self, request):
        """
        GET: Get a list of words belonging to the current user.
        """
        words = Word.objects.filter(user=request.user) 
        
        serializer = WordSerializer(words, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @time_logger
    def post(self, request):
        """
        POST: Add a new word for the current user.
        Automatically detects word_type if not provided.
        """
        data = request.data.copy()

        if not data.get('word_type') and data.get('word'):
            word = data['word'].strip()
            api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    json_data = response.json()
                    meanings = json_data[0].get('meanings', [])
                    if meanings:
                        data['word_type'] = meanings[0].get('partOfSpeech', 'other')
                    else:
                        data['word_type'] = 'other'
                else:
                    data['word_type'] = 'other'
            except Exception:
                data['word_type'] = 'other'

        serializer = WordSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WordDetailView(APIView):
    """
    DELETE — Delete a word by id
    PUT — Fully update a word by id
    PATCH — Partially update a word by id
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        """
        Auxiliary function for obtaining an object 
        belonging to the user or returning 404.
        """
        obj = get_object_or_404(Word, pk=pk, user=request.user)
        return obj

    @time_logger
    def put(self, request, pk):
        """
        PUT: Completely update the word by id.
        """
        word_to_update = self.get_object(request, pk)
        serializer = WordSerializer(word_to_update, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @time_logger
    def patch(self, request, pk):
        """
        PATCH: Partially update the word by id.
        """
        word_to_update = self.get_object(request, pk)
        serializer = WordSerializer(word_to_update, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @time_logger
    def delete(self, request, pk):
        """
        DELETE: Delete a word by id.
        """
        try:
            word_to_delete = self.get_object(request, pk)
            word_to_delete.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Word.DoesNotExist:
             return Response(
                 {'error': 'Word not found or you do not have permission'},
                 status=status.HTTP_404_NOT_FOUND
             )