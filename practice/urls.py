from django.urls import path
from . import views

urlpatterns = [
    path('practice/', views.practice_view, name='practice'),
    path('practice/reading/', views.reading_view, name='practice_reading'),
    path('practice/reading/<int:text_id>/', views.reading_text_view, name='reading_text'),
    path('word/<int:text_id>/<str:word>/', views.word_detail_view, name='word_detail'),
    path('add_text/', views.text_add_view, name='add_text'),
    path('edit_text/<int:text_id>/', views.EditTextView.as_view(), name='edit_text'),
    path('practice/groups/', views.parct_groups_view, name='practice_groups'),
    path('practice/groups/<int:group_id>/', views.PracticeGroupWordsListView.as_view(), name='group_words_practice'),
    path('add_as_uses/<int:group_id>/', views.add_as_uses, name='add_as_uses'),
    path('leave_group/<int:group_id>/<str:fp>/', views.leave_group, name='leave_group'),
    path('save_word/<int:group_id>/<int:word_id>/', views.save_word, name='save_word'),
    path('save-group-words/<int:group_id>/', views.save_group_words, name='save_group_words'),
    path('pending_requests/', views.pending_group_requests, name='pending_requests'),
    path('send_grooup_request/<int:group_id>/', views.send_group_request, name='send_group_request'),
    path('approve_group_request/<int:group_id>/', views.approve_group_request, name='approve_group_request'),
    path('delete_group_request/<int:group_id>/', views.reject_group_request, name='delete_group_request'),
]