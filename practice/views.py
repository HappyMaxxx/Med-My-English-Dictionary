import re
import string
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from .forms import TextForm
from django.views.generic import ListView
from django.views import View
from django.db.models import Min, Max

from django.core.paginator import Paginator

from urllib.parse import urlparse
from django.contrib.auth.mixins import LoginRequiredMixin

from med.models import *
from dictionary.models import Word, WordGroup
from .models import CommunityGroup, ReadingText

from med.views import add_to_main_group
from achievements.views import process_interaction_achivments
from notifications.views import create_notification

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

practice_cards = {
    'test': {
        'word': 'Test',
        'img': 'practice/img/dice_light.png',
        'dark_img': 'practice/img/dice_dark.png',
        'href': 'soon'
    },
    'reading': {
        'word': 'Reading',
        'img': 'practice/img/read_light.svg',
        'dark_img': 'practice/img/read_dark.svg',
        'href': 'practice_reading'
    },
    'groups': {
        'word': 'Groups',
        'img': 'practice/img/group_light.svg',
        'dark_img': 'practice/img/group_dark.svg',
        'href': 'practice_groups'
    },
}

def practice_view(request):
    return render(request, 'practice/practice.html', {'cards': practice_cards.values()})

def reading_view(request):
    texts = ReadingText.objects.all()
    
    word_stats = texts.aggregate(min_words=Min('word_count'), max_words=Max('word_count'))
    min_words = word_stats['min_words'] or 0 
    max_words = word_stats['max_words'] or 0

    if request.method == 'GET':
        if 'words_min' not in request.GET or 'words_max' not in request.GET:
            query_params = request.GET.copy()
            if 'words_min' not in request.GET:
                query_params['words_min'] = min_words
            if 'words_max' not in request.GET:
                query_params['words_max'] = max_words
            return HttpResponseRedirect(f"{request.path}?{query_params.urlencode()}")

    level = request.GET.get('level')
    if level:
        texts = texts.filter(eng_level=level)

    words_min = request.GET.get('words_min', min_words)
    if words_min:
        texts = texts.filter(word_count__gte=int(words_min))

    words_max = request.GET.get('words_max', max_words)
    if words_max:
        texts = texts.filter(word_count__lte=int(words_max))

    paginator = Paginator(texts, 25)
    page_number = request.GET.get('page')
    paginated_texts = paginator.get_page(page_number)

    levels = ReadingText.ENG_LEVEL_CHOICES

    return render(request, 'practice/reading.html', {
        'texts': paginated_texts,
        'paginator': paginator,
        'page_obj': paginated_texts,
        'levels': levels,
        'min_words': min_words,
        'max_words': max_words,
    })

def parct_groups_view(request):
    groups = CommunityGroup.objects.filter(state='added').select_related('group')

    for group in groups:
        group.words_count = group.group.words.count()
    
    groups = sorted(groups, key=lambda x: x.words_count)

    paginator = Paginator(groups, 25)
    page_number = request.GET.get('page')
    paginated_groups = paginator.get_page(page_number)
    page_obj = paginator.get_page(page_number)

    return render(request, 'practice/practice_groups.html', {'groups': paginated_groups, 'paginator': paginator, 'page_obj': page_obj})

def split_content_by_phrases(content, translations):
    """
    Splits the text into words and attaches translations.
    Works with both dict {"word": "translation"} and list [{"word": "...", "translation": "..."}].
    """

    # Normalize translations to a dict
    if isinstance(translations, list):
        # if translations is a list of dicts
        translations = {item["word"]: item["translation"] for item in translations if "word" in item and "translation" in item}
    elif not isinstance(translations, dict):
        # if translations is None or something else → make it empty dict
        translations = {}

    lower_translations = {k.lower(): v for k, v in translations.items()}

    words = content.split()

    phrases = []
    for word in words:
        # remove punctuation and lowercase for lookup
        clean_word = word.strip(".,!?;:").lower()
        translation = lower_translations.get(clean_word)
        phrases.append({
            "word": word,
            "translation": translation if translation else None
        })

    return phrases

def reading_text_view(request, text_id):
    text = get_object_or_404(ReadingText, id=text_id)
    base_url = None
    if text.is_auth_a:
        url = text.auth
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    content_phrases = []
    for paragraph in text.content.splitlines():
        phrases = split_content_by_phrases(paragraph, text.words_with_translations)
        content_phrases.append(phrases)

    paginator = Paginator(content_phrases, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    user_profile = UserProfile.objects.get(user=request.user)
    user_profile.text_read += 1
    user_profile.save()

    return render(request, 'practice/read_text.html', {
        'text': text,
        'base_url': base_url,
        'page_obj': page_obj,
        'paginator': paginator,
    })

def word_detail_view(request, word, text_id):
    text = get_object_or_404(ReadingText, content__icontains=word, id=text_id)

    translations = text.words_with_translations

    translation = None
    if isinstance(translations, dict):
        # case: stored as {"word": "translation"}
        translation = translations.get(word.lower())
    elif isinstance(translations, list):
        # case: stored as [{"word": "...", "translation": "..."}]
        for item in translations:
            if item.get("word", "").lower() == word.lower():
                translation = item.get("translation")
                break

    if not translation:
        translation = "The translation is not found"

    sentences = re.split(r'(?<=[.!?])[\s\n]+', text.content)
    example_sentence = next((sentence for sentence in sentences if word in sentence), "The example sentence is not found")

    return render(
        request,
        "practice/word_detail.html",
        {
            "word": word,
            "translation": translation,
            "example": example_sentence,
            "text_id": text_id,
        },
    )

def word_couner(text):
    words = text.split()
    return len(words)

def time_counter(words):
    return round(words / 60)

def text_add_view(request):
    form = TextForm()

    if request.method == 'POST':
        form = TextForm(request.POST)
        word_count = word_couner(form.data['content'])
        time_count = time_counter(word_count)
        if form.is_valid():
            form.instance.word_count = word_count
            form.instance.time_to_read = time_count
            form.save()
            return redirect('practice_reading')
        
    return render(request, 'practice/add_text.html', {'form': form})


class EditTextView(LoginRequiredMixin, View):
    def get(self, request, text_id, *args, **kwargs):
        text = get_object_or_404(ReadingText, id=text_id)
        form = TextForm(instance=text)
        return render(request, 'practice/edit_text.html', {'form': form, 'text': text})

    def post(self, request, text_id, *args, **kwargs):
        text = get_object_or_404(ReadingText, id=text_id)
        form = TextForm(request.POST, instance=text)
        word_count = word_couner(form.data['content'])
        time_count = time_counter(word_count)
        if form.is_valid():
            form.instance.word_count = word_count
            form.instance.time_to_read = time_count
            form.save()
            return redirect('reading_text', text_id=text_id)
        return render(request, 'practice/edit_text.html', {'form': form, 'text': text})


class PracticeGroupWordsListView(LoginRequiredMixin, ListView):
    model = Word
    template_name = 'practice/group_words.html'
    context_object_name = 'words'
    paginate_by = 25

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)

        user_word_titles = [word.word.lower() for word in Word.objects.filter(user=self.request.user)]

        words = group.words.all()
        for word in words:
                word.is_saved = word.word.lower() in user_word_titles

        return words
    
    def get_context_data(self, **kwargs):
        process_interaction_achivments(self.request.user)

        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        context['group'] = group
        context['is_usses'] = group.uses_users.filter(id=self.request.user.id).exists()
        if CommunityGroup.objects.filter(group=context['group'], state='added').exists():
            context['is_community'] = True
        else:
            context['is_community'] = False
        return context
    
def add_as_uses(request, group_id):
    group = get_object_or_404(WordGroup, id=group_id)
    group.uses_users.add(request.user)
    return redirect('group_words_practice', group_id=group_id)

def leave_group(request, group_id, fp):

    if fp.lower() in ['true', '1', 'yes']:
        is_fp = True
    elif fp.lower() in ['false', '0', 'no']:
        is_fp = False

    group = get_object_or_404(WordGroup, id=group_id)
    group.uses_users.remove(request.user)
    if is_fp:
        return redirect('group_words_practice', group_id=group_id)
    return redirect('groups')

def save_word(request, group_id, word_id):
    word = get_object_or_404(Word, id=word_id)
    existing_word = Word.objects.filter(user=request.user, id=word.id).first()

    if not existing_word:
        Word.objects.create(user=request.user, word=word.word, translation=word.translation,
                            word_type=word.word_type, example=word.example, is_favourite=False)

        new_word = Word.objects.get(word=word.word, user=request.user)

        add_to_main_group(request, new_word)

    if group_id:
        return redirect('group_words_practice', group_id=group_id)
    else:
        return redirect('words', user_name=request.user.username)

def save_group_words(request, group_id):
    user = request.user
    group = get_object_or_404(WordGroup, id=group_id)
    words = group.words.all()
    word_ids = [word.id for word in words]
    group_name = f"All {user.username}'s "
    all_my_words = Word.objects.filter(user=user)

    new_group = WordGroup.objects.create(
        name=f"{group.name}",
        user=user
    )

    for word_id in word_ids:
        original_word = get_object_or_404(Word, id=word_id)

        if not all_my_words.filter(word=original_word.word).exists():
            copied_word = Word.objects.create(
                word=original_word.word,
                translation=original_word.translation,
                example=original_word.example,
                word_type=original_word.word_type,
                user=user,
            )
            
            # all words groop
            group1, created = WordGroup.objects.get_or_create(
                name=group_name,
                is_main=True,
                user=user
            )

            group1.words.add(copied_word)

            new_group.words.add(copied_word)

        else:
            word = all_my_words.get(word=original_word.word)
            new_group.words.add(word)
    
    group.uses_users.remove(user)
    return redirect('groups')

def send_group_request(request, group_id):
    group = get_object_or_404(WordGroup, id=group_id, user=request.user)

    CommunityGroup.objects.create(
        group=group,
        state='pending',
    )
    
    return redirect('group_words', group_id=group_id)

def approve_group_request(request, group_id):
    group = get_object_or_404(CommunityGroup, group_id=group_id)
    group.state = 'added'
    group.save()

    create_notification(
        receiver=group.group.user,
        message=f"Your group {group.group.name} was approved",
    )

    return redirect('practice_groups')

def reject_group_request(request, group_id):
    CommunityGroup.objects.filter(group_id=group_id).delete()
    group = get_object_or_404(WordGroup, id=group_id)

    create_notification(
        receiver=group.user,
        message=f"Your group {group.name} was rejected",
    )

    return redirect('practice_groups')

def pending_group_requests(request):
    if not request.user.is_staff:
        return redirect('profile', user_name=request.user.username)
    
    pending_requests = CommunityGroup.objects.filter(state='pending')

    return render(request, 'practice/pending_group_requests.html', {'pending_requests': pending_requests})