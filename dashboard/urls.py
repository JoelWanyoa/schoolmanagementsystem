from django.urls import path
from . import views

urlpatterns = [
     # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('analytics/students/', views.student_analytics, name='student_analytics'),

    # Initial Setup
    path('setup/', views.initial_setup, name='initial_setup'),
    path('setup/create-classes/', views.create_initial_classes, name='create_initial_classes'),
    path('setup/create-sections/', views.create_initial_sections, name='create_initial_sections'),
    path('setup/create-academic-years/', views.create_initial_academic_years, name='create_initial_academic_years'),
    path('setup/complete/', views.complete_setup, name='complete_setup'),
    # Finances
    path('financial-overview/', views.financial_overview, name='financial_overview'),
    path('expense-management/', views.expense_management, name='expense_management'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('edit-expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('expense-detail/<int:expense_id>/', views.expense_detail, name='expense_detail'),
    path('expense-statistics/', views.expense_statistics, name='expense_statistics'),

    # Fees
    path('all-fees/', views.all_fees, name='all_fees'),
    path('fee-detail/<int:fee_id>/', views.fee_detail, name='fee_detail'),
    path('edit-fee/<int:fee_id>/', views.edit_fee, name='edit_fee'),
    path('mark-paid/<int:fee_id>/', views.mark_paid, name='mark_paid'),
    path('delete-fee/<int:fee_id>/', views.delete_fee, name='delete_fee'),
    path('add-fee/', views.add_fee, name='add_fee'),
    
    # Students DRUD
    path('students/', views.all_students, name='all_students'),
    path('students/admit/', views.admit_form, name='admit_form'),
    path('students/details/<str:student_id>/', views.student_details, name='student_details'),
    path('students/<str:student_id>/update/', views.update_student, name='update_student'),
    path('students/<str:student_id>/delete/', views.delete_student, name='delete_student'),
    path('students/<str:student_id>/restore/', views.restore_student, name='restore_student'),
    path('students/<str:student_id>/permanent-delete/', views.permanent_delete_student, name='permanent_delete_student'),
    path('students/promotion/', views.student_promotion, name='student_promotion'),
    
    # Admissions Management (MISSING)
    path('students/admissions/', views.manage_admissions, name='manage_admissions'),
    path('students/admissions/approve/<int:admission_id>/', views.approve_admission, name='approve_admission'),
    

    # Parents
    path('parents/', views.all_parents, name='all_parents'),
    path('parents/details/<int:parent_id>/', views.parent_details, name='parent_details'),
    # Parent functionality URLs
    path('parents/send-message/<int:parent_id>/', views.send_message_to_parent, name='send_message_to_parent'),
    path('parents/link-children/<int:parent_id>/', views.link_children_to_parent, name='link_children_to_parent'),
    path('parents/fee-history/<int:parent_id>/', views.parent_fee_history, name='parent_fee_history'),
    path('parents/unlink-child/<int:parent_id>/<int:student_id>/', views.unlink_child, name='unlink_child'),
    path('parents/add-student/<int:parent_id>/', views.add_student_to_parent, name='add_student_to_parent'),

    # Teachers
    path('teachers/', views.all_teachers, name='all_teachers'),
    path('teachers/details/<str:teacher_id>/', views.teacher_details, name='teacher_details'),  # Fixed: Added parameter
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/payment/', views.teacher_payment, name='teacher_payment'),
    
    # UI Elements
    path('ui/buttons/', views.buttons, name='buttons'),
    path('ui/modals/', views.modals, name='modals'),
    
    # Communication
    # Messages
    path('messaging/', views.messaging, name='messaging'),
    path('messaging/get-conversation-messages/<int:user_id>/', views.get_conversation_messages, name='get_conversation_messages'),
    path('messaging/send-message-ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('messaging/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('messaging/download-file/<int:message_id>/', views.download_message_file, name='download_message_file'),
    
    # Notices
    path('notice-board/', views.notice_board, name='notice_board'),
    path('create-notice-ajax/', views.create_notice_ajax, name='create_notice_ajax'),
    path('update-notice-ajax/', views.update_notice_ajax, name='update_notice_ajax'),
    path('delete-notice-ajax/', views.delete_notice_ajax, name='delete_notice_ajax'),
    
    # Account
    path('account-settings/', views.account_settings, name='account_settings'),
    
    # AJAX/API Endpoints (MISSING - CRITICAL)
    # path('ajax/sections-by-class/<int:class_id>/', views.get_sections_by_class, name='get_sections_by_class'),
    path('ajax/check-username/', views.check_username_availability, name='check_username_availability'),
    path('ajax/check-email/', views.check_email_availability, name='check_email_availability'),
]