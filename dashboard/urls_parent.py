from django.urls import path
from . import views
from core.decorators import parent_required

urlpatterns = [
    path('', parent_required(views.parent_dashboard), name='parent_dashboard'),

    # Parent Profile & Children
    path('parents/details/<int:parent_id>/', parent_required(views.parent_details), name='parent_details'),
    path('parents/fee-history/<int:parent_id>/', parent_required(views.parent_fee_history), name='parent_fee_history'),
    path('parents/link-children/<int:parent_id>/', parent_required(views.link_children_to_parent), name='link_children_to_parent'),
    path('parents/add-student/<int:parent_id>/', parent_required(views.add_student_to_parent), name='add_student_to_parent'),
    path('parents/send-message/<int:parent_id>/', views.send_message_to_parent, name='send_message_to_parent'),
    path('parents/link-children/<int:parent_id>/', views.link_children_to_parent, name='link_children_to_parent'),
    path('parents/fee-history/<int:parent_id>/', views.parent_fee_history, name='parent_fee_history'),
    path('parents/unlink-child/<int:parent_id>/<int:student_id>/', views.unlink_child, name='unlink_child'),
    path('parents/add-student/<int:parent_id>/', views.add_student_to_parent, name='add_student_to_parent'),


    # Messaging
    path('messaging/', parent_required(views.messaging), name='messaging'),
    path('messaging/get-conversation-messages/<int:user_id>/', parent_required(views.get_conversation_messages), name='get_conversation_messages'),
    path('messaging/send-message-ajax/', parent_required(views.send_message_ajax), name='send_message_ajax'),
]
