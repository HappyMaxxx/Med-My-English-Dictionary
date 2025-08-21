from django.urls import path
from . import views

urlpatterns = [
    # WORDS LOGIC
    path('addword/', views.AddWordView.as_view(), name='addword'),
    path('words/<slug:user_name>', views.WordListView.as_view(), name='words'),
    path('edit_word/<int:word_id>/', views.EditWordView.as_view(), name='edit_word'),
    path('make_favourite/<int:word_id>/', views.make_favourite, name='make_favourite'),
    path('save_words/', views.save_all_words_as_json, name='save_words'),
    path('find_word_type/', views.find_word_type, name='find_word_type'),
    path('check_word/', views.check_word, name='check_word'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('upload/', views.upload_file, name='upload_file'),
    # GROUPS LOGIC
    path('groups/', views.GroupListView.as_view(), name='groups'),
    path('groups/<int:group_id>/', views.GroupWordsView.as_view(), name='group_words'),
    path('create_group/', views.CreateGroupView.as_view(), name='create_group'),
    path('select_group/', views.SelectGroupView.as_view(), name='select_group'),
]
