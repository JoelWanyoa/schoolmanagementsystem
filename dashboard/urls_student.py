from django.urls import path
from . import views
from core.decorators import student_required

urlpatterns = [
    path('', student_required(views.student_dashboard), name='student_dashboard'),

    # Student Profile & Academic
    path('details/<str:student_id>/', student_required(views.student_details), name='student_details'),
    # path('students/grades/', student_required(views.student_grades), name='student_grades'),
    # path('students/attendance/', student_required(views.student_attendance), name='student_attendance'),
    # path('students/report-card/', student_required(views.view_report_card), name='view_report_card'),

    # Messaging
    path('messaging/', student_required(views.messaging), name='messaging'),
    path('messaging/get-conversation-messages/<int:user_id>/', student_required(views.get_conversation_messages), name='get_conversation_messages'),
    path('messaging/send-message-ajax/', student_required(views.send_message_ajax), name='send_message_ajax'),
]
