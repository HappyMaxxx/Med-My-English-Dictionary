from rest_framework import serializers
from dictionary.models import Word

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fielsd = ('id', 'word', 'translation', 'example', 'time_create', 'time_update',
                  'is_favourite', 'word_type')
        read_only_fields = ('id',)