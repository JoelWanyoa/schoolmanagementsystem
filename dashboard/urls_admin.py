from django.urls import path
from . import views
from core.decorators import admin_required

urlpatterns = [
    # Dashboard
    path('', admin_required(views.dashboard), name='dashboard'),

    # Initial Setup
    path('setup/', admin_required(views.initial_setup), name='initial_setup'),
    path('setup/create-classes/', admin_required(views.create_initial_classes), name='create_initial_classes'),
    path('setup/create-sections/', admin_required(views.create_initial_sections), name='create_initial_sections'),
    path('setup/create-academic-years/', admin_required(views.create_initial_academic_years), name='create_initial_academic_years'),
    path('setup/complete/', admin_required(views.complete_setup), name='complete_setup'),

    # Finances
    path('financial-overview/', admin_required(views.financial_overview), name='financial_overview'),
    path('expense-management/', admin_required(views.expense_management), name='expense_management'),
    path('add-expense/', admin_required(views.add_expense), name='add_expense'),
    path('edit-expense/<int:expense_id>/', admin_required(views.edit_expense), name='edit_expense'),
    path('delete-expense/<int:expense_id>/', admin_required(views.delete_expense), name='delete_expense'),
    path('expense-detail/<int:expense_id>/', admin_required(views.expense_detail), name='expense_detail'),
    path('expense-statistics/', admin_required(views.expense_statistics), name='expense_statistics'),

    # Fees Management
    path('fees/all-fees/', admin_required(views.all_fees), name='all_fees'),
    path('fees/fee-detail/<int:fee_id>/', admin_required(views.fee_detail), name='fee_detail'),
    path('fees/edit-fee/<int:fee_id>/', admin_required(views.edit_fee), name='edit_fee'),
    path('fees/mark-paid/<int:fee_id>/', admin_required(views.mark_paid), name='mark_paid'),
    path('fees/delete-fee/<int:fee_id>/', admin_required(views.delete_fee), name='delete_fee'),
    path('add-fee/', admin_required(views.add_fee), name='add_fee'),
    path('fees/bulk-actions/', admin_required(views.bulk_fee_actions), name='bulk_fee_actions'),
    path('fees/reminders/', admin_required(views.fee_reminders), name='fee_reminders'),
    path('fees/send-bulk-reminders/', admin_required(views.send_bulk_reminders), name='send_bulk_reminders'),
    path('fees/mark-bulk-paid/', admin_required(views.mark_bulk_paid), name='mark_bulk_paid'),
    path('fees/send-reminder/<int:fee_id>/', admin_required(views.send_fee_reminder), name='send_fee_reminder'),

    # Students Management
    path('students/', admin_required(views.all_students), name='all_students'),
    path('students/admit/', admin_required(views.admit_form), name='admit_form'),
    path('students/details/<str:student_id>/', admin_required(views.student_details), name='student_details'),
    path('students/<str:student_id>/update/', admin_required(views.update_student), name='update_student'),
    path('students/<str:student_id>/delete/', admin_required(views.delete_student), name='delete_student'),
    path('students/<str:student_id>/restore/', admin_required(views.restore_student), name='restore_student'),
    path('students/<str:student_id>/permanent-delete/', admin_required(views.permanent_delete_student), name='permanent_delete_student'),
    path('students/promotion/', admin_required(views.student_promotion), name='student_promotion'),
    path('students/promotion-history/', admin_required(views.promotion_history), name='promotion_history'),

    # Admissions Management
    path('students/admissions/', admin_required(views.manage_admissions), name='manage_admissions'),
    path('students/admissions/approve/<int:admission_id>/', admin_required(views.approve_admission), name='approve_admission'),
    path('students/admissions/reject/<int:admission_id>/', admin_required(views.reject_admission), name='reject_admission'),
    path('students/admissions/<int:admission_id>/', admin_required(views.admission_details), name='admission_details'),

    # Parents Management
    path('parents/', admin_required(views.all_parents), name='all_parents'),
    path('parents/details/<int:parent_id>/', admin_required(views.parent_details), name='parent_details'),
    path('parents/add/', admin_required(views.add_parent), name='add_parent'),
    path('parents/<int:parent_id>/update/', admin_required(views.update_parent), name='update_parent'),
    path('parents/<int:parent_id>/delete/', admin_required(views.delete_parent), name='delete_parent'),

    # Teachers Management
    path('teachers/', admin_required(views.all_teachers), name='all_teachers'),
    path('teachers/details/<str:teacher_id>/', admin_required(views.teacher_details), name='teacher_details'),
    path('teachers/add/', admin_required(views.add_teacher), name='add_teacher'),
    path('teachers/<str:teacher_id>/update/', admin_required(views.update_teacher), name='update_teacher'),
    path('teachers/<str:teacher_id>/delete/', admin_required(views.delete_teacher), name='delete_teacher'),
    path('teachers/<str:teacher_id>/assign-classes/', admin_required(views.assign_teacher_classes), name='assign_teacher_classes'),
    path('teachers/<str:teacher_id>/remove-class/<int:class_id>/', admin_required(views.remove_teacher_class), name='remove_teacher_class'),
    path('teachers/payment/', admin_required(views.teacher_payment), name='teacher_payment'),
    path('teachers/payment/<int:payment_id>/', admin_required(views.teacher_payment_detail), name='teacher_payment_detail'),
    path('teachers/payment/add/', admin_required(views.add_teacher_payment), name='add_teacher_payment'),

    # Academic Management
    path('academic/classes/', admin_required(views.manage_classes), name='manage_classes'),
    path('academic/classes/add/', admin_required(views.add_class), name='add_class'),
    path('academic/classes/<int:class_id>/edit/', admin_required(views.edit_class), name='edit_class'),
    path('academic/classes/<int:class_id>/delete/', admin_required(views.delete_class), name='delete_class'),
    path('academic/subjects/', admin_required(views.manage_subjects), name='manage_subjects'),
    path('academic/subjects/add/', admin_required(views.add_subject), name='add_subject'),
    path('academic/subjects/<int:subject_id>/edit/', admin_required(views.edit_subject), name='edit_subject'),
    path('academic/subjects/<int:subject_id>/delete/', admin_required(views.delete_subject), name='delete_subject'),
    path('academic/timetable/', admin_required(views.manage_timetable), name='manage_timetable'),
    path('academic/timetable/generate/', admin_required(views.generate_timetable), name='generate_timetable'),
    path('academic/timetable/<int:class_id>/', admin_required(views.class_timetable), name='class_timetable'),

    # Library Management
    path('library/books/', admin_required(views.all_books), name='all_books'),
    path('library/books/add/', admin_required(views.add_book), name='add_book'),
    path('library/books/<int:book_id>/', admin_required(views.book_detail), name='book_detail'),
    path('library/books/<int:book_id>/edit/', admin_required(views.edit_book), name='edit_book'),
    path('library/books/<int:book_id>/delete/', admin_required(views.delete_book), name='delete_book'),
    path('library/borrow/', admin_required(views.borrow_book), name='borrow_book'),
    path('library/return/<int:borrow_id>/', admin_required(views.return_book), name='return_book'),

    # Examination Management
    path('examinations/schedule/', admin_required(views.exam_schedule), name='exam_schedule'),
    path('examinations/schedule/create/', admin_required(views.create_exam_schedule), name='create_exam_schedule'),
    path('examinations/grades/', admin_required(views.exam_grades), name='exam_grades'),
    path('examinations/grades/setup/', admin_required(views.setup_grading_system), name='setup_grading_system'),

    # Transport Management
    path('transport/', admin_required(views.transport_management), name='transport_management'),
    path('transport/routes/', admin_required(views.transport_routes), name='transport_routes'),
    path('transport/vehicles/', admin_required(views.transport_vehicles), name='transport_vehicles'),
    path('transport/assign/', admin_required(views.assign_transport), name='assign_transport'),

    # Hostel Management
    path('hostel/', admin_required(views.hostel_management), name='hostel_management'),
    path('hostel/rooms/', admin_required(views.hostel_rooms), name='hostel_rooms'),
    path('hostel/allocations/', admin_required(views.hostel_allocations), name='hostel_allocations'),
    path('hostel/allocate/', admin_required(views.allocate_hostel), name='allocate_hostel'),

    # UI Elements
    path('ui/buttons/', admin_required(views.buttons), name='buttons'),
    path('ui/modals/', admin_required(views.modals), name='modals'),
    path('ui/alerts/', admin_required(views.alerts), name='alerts'),
    path('ui/grid/', admin_required(views.grid), name='grid'),
    path('ui/progress-bars/', admin_required(views.progress_bars), name='progress_bars'),

    # Notices & Messaging
    path('notice-board/', admin_required(views.notice_board), name='notice_board'),
    path('create-notice-ajax/', admin_required(views.create_notice_ajax), name='create_notice_ajax'),
    path('update-notice-ajax/', admin_required(views.update_notice_ajax), name='update_notice_ajax'),
    path('delete-notice-ajax/', admin_required(views.delete_notice_ajax), name='delete_notice_ajax'),

    path('messaging/', admin_required(views.messaging), name='messaging'),
    path('messaging/get-conversation-messages/<int:user_id>/', admin_required(views.get_conversation_messages), name='get_conversation_messages'),
    path('messaging/send-message-ajax/', admin_required(views.send_message_ajax), name='send_message_ajax'),
    path('messaging/mark-all-read/', admin_required(views.mark_all_read), name='mark_all_read'),
    path('messaging/download-file/<int:message_id>/', admin_required(views.download_message_file), name='download_message_file'),

    # Account Settings
    path('account-settings/', admin_required(views.account_settings), name='account_settings'),

    # AJAX / API
    path('ajax/sections-by-class/<int:class_id>/', admin_required(views.get_sections_by_class), name='get_sections_by_class'),
    path('ajax/check-username/', admin_required(views.check_username_availability), name='check_username_availability'),
    path('ajax/check-email/', admin_required(views.check_email_availability), name='check_email_availability'),
    path('ajax/get-students-by-class/<int:class_id>/', admin_required(views.get_students_by_class), name='get_students_by_class'),
    path('ajax/get-subjects-by-class/<int:class_id>/', admin_required(views.get_subjects_by_class), name='get_subjects_by_class'),
]
