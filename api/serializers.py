from rest_framework import serializers
from dictionary.models import Word

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ('id', 'word', 'translation', 'example', 'word_type',
                  'time_create', 'time_update', 'is_favourite')
        read_only_fields = ('id',)