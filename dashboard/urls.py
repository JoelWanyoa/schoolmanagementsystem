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
    path('fees/all-fees/', views.all_fees, name='all_fees'),
    path('fees/fee-detail/<int:fee_id>/', views.fee_detail, name='fee_detail'),
    path('fees/edit-fee/<int:fee_id>/', views.edit_fee, name='edit_fee'),
    path('fees/mark-paid/<int:fee_id>/', views.mark_paid, name='mark_paid'),
    path('fees/delete-fee/<int:fee_id>/', views.delete_fee, name='delete_fee'),
    path('add-fee/', views.add_fee, name='add_fee'),
    path('fees/bulk-actions/', views.bulk_fee_actions, name='bulk_fee_actions'),
    path('fees/reminders/', views.fee_reminders, name='fee_reminders'),
    path('fees/send-bulk-reminders/', views.send_bulk_reminders, name='send_bulk_reminders'),
    path('fees/mark-bulk-paid/', views.mark_bulk_paid, name='mark_bulk_paid'),
    path('fees/send-reminder/<int:fee_id>/', views.send_fee_reminder, name='send_fee_reminder'),

    # Students DRUD
    path('students/', views.all_students, name='all_students'),
    path('students/admit/', views.admit_form, name='admit_form'),
    path('students/details/<str:student_id>/', views.student_details, name='student_details'),
    path('students/<str:student_id>/update/', views.update_student, name='update_student'),
    path('students/<str:student_id>/delete/', views.delete_student, name='delete_student'),
    path('students/<str:student_id>/restore/', views.restore_student, name='restore_student'),
    path('students/<str:student_id>/permanent-delete/', views.permanent_delete_student, name='permanent_delete_student'),
    path('students/promotion/', views.student_promotion, name='student_promotion'),
    path('students/promotion-history/', views.promotion_history, name='promotion_history'),
    
    # Admissions Management
    path('students/admissions/', views.manage_admissions, name='manage_admissions'),
    path('students/admissions/approve/<int:admission_id>/', views.approve_admission, name='approve_admission'),
    path('students/admissions/reject/<int:admission_id>/', views.reject_admission, name='reject_admission'),
    path('students/admissions/<int:admission_id>/', views.admission_details, name='admission_details'),

    # Parents
    path('parents/', views.all_parents, name='all_parents'),
    path('parents/details/<int:parent_id>/', views.parent_details, name='parent_details'),
    path('parents/add/', views.add_parent, name='add_parent'),
    path('parents/<int:parent_id>/update/', views.update_parent, name='update_parent'),
    path('parents/<int:parent_id>/delete/', views.delete_parent, name='delete_parent'),
    # Parent functionality URLs
    path('parents/send-message/<int:parent_id>/', views.send_message_to_parent, name='send_message_to_parent'),
    path('parents/link-children/<int:parent_id>/', views.link_children_to_parent, name='link_children_to_parent'),
    path('parents/fee-history/<int:parent_id>/', views.parent_fee_history, name='parent_fee_history'),
    path('parents/unlink-child/<int:parent_id>/<int:student_id>/', views.unlink_child, name='unlink_child'),
    path('parents/add-student/<int:parent_id>/', views.add_student_to_parent, name='add_student_to_parent'),

    # Teachers
    path('teachers/', views.all_teachers, name='all_teachers'),
    path('teachers/details/<str:teacher_id>/', views.teacher_details, name='teacher_details'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/<str:teacher_id>/update/', views.update_teacher, name='update_teacher'),
    path('teachers/<str:teacher_id>/delete/', views.delete_teacher, name='delete_teacher'),
    # Teacher class assignment URLs
    path('teachers/<str:teacher_id>/assign-classes/', views.assign_teacher_classes, name='assign_teacher_classes'),
    path('teachers/<str:teacher_id>/remove-class/<int:class_id>/', views.remove_teacher_class, name='remove_teacher_class'),
    path('teachers/payment/', views.teacher_payment, name='teacher_payment'),
    path('teachers/payment/<int:payment_id>/', views.teacher_payment_detail, name='teacher_payment_detail'),
    path('teachers/payment/add/', views.add_teacher_payment, name='add_teacher_payment'),
    
    # Teacher Dashboard URLs
    path('teacher/my-classes/', views.teacher_my_classes, name='teacher_my_classes'),
    path('teacher/class-schedule/', views.teacher_class_schedule, name='teacher_class_schedule'),
    path('teacher/my-students/', views.teacher_my_students, name='teacher_my_students'),
    path('teacher/attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/exam-results/', views.teacher_exam_results, name='teacher_exam_results'),

    # Assignment URLs
    path('teacher/assignments/create/', views.assignment_create, name='assignment_create'),
    path('teacher/assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('teacher/assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('teacher/assignments/<int:assignment_id>/delete/', views.assignment_delete, name='assignment_delete'),
    path('teacher/assignments/<int:assignment_id>/download-submissions/', views.assignment_download_submissions, name='assignment_download_submissions'),
    
    # Teacher AJAX endpoints
    path('teacher/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/get-class-students/<int:class_id>/', views.get_class_students, name='get_class_students'),

    # Exam Management URLs
    path('teacher/exams/', views.teacher_exam_management, name='teacher_exam_management'),
    path('teacher/exams/create/', views.create_exam, name='create_exam'),
    path('teacher/exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('teacher/exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),
    path('teacher/exams/<int:exam_id>/enter-marks/', views.enter_marks, name='enter_marks'),
    path('teacher/exams/<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('teacher/exams/<int:exam_id>/analysis/', views.exam_analysis, name='exam_analysis'),
    path('teacher/exams/<int:exam_id>/export-excel/', views.export_results_excel, name='export_results_excel'),
    path('teacher/exams/<int:exam_id>/export-pdf/', views.export_results_pdf, name='export_results_pdf'),
    path('teacher/exams/<int:exam_id>/bulk-upload/', views.bulk_upload_results, name='bulk_upload_results'),
    
    path('teacher/subject-results/', views.subject_results, name='subject_results'),
    path('teacher/subject-results/<int:subject_id>/', views.subject_results, name='subject_results_detail'),
    path('teacher/class-results/', views.class_results, name='class_results'),
    path('teacher/class-results/<int:class_id>/', views.class_results, name='class_results_detail'),
    path('teacher/report-card/<int:student_id>/', views.generate_report_card, name='generate_report_card'),
    path('teacher/report-card/<int:student_id>/<str:term>/', views.generate_report_card, name='generate_report_card_term'),
    
    # Academic Management (Missing URLs)
    path('academic/classes/', views.manage_classes, name='manage_classes'),
    path('academic/classes/add/', views.add_class, name='add_class'),
    path('academic/classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('academic/classes/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    
    path('academic/subjects/', views.manage_subjects, name='manage_subjects'),
    path('academic/subjects/add/', views.add_subject, name='add_subject'),
    path('academic/subjects/<int:subject_id>/edit/', views.edit_subject, name='edit_subject'),
    path('academic/subjects/<int:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    path('academic/timetable/', views.manage_timetable, name='manage_timetable'),
    path('academic/timetable/generate/', views.generate_timetable, name='generate_timetable'),
    path('academic/timetable/<int:class_id>/', views.class_timetable, name='class_timetable'),
    
    # Library Management (Missing URLs)
    path('library/books/', views.all_books, name='all_books'),
    path('library/books/add/', views.add_book, name='add_book'),
    path('library/books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('library/books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('library/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('library/borrow/', views.borrow_book, name='borrow_book'),
    path('library/return/<int:borrow_id>/', views.return_book, name='return_book'),
    
    # Examination Management (Missing URLs)
    path('examinations/schedule/', views.exam_schedule, name='exam_schedule'),
    path('examinations/schedule/create/', views.create_exam_schedule, name='create_exam_schedule'),
    path('examinations/grades/', views.exam_grades, name='exam_grades'),
    path('examinations/grades/setup/', views.setup_grading_system, name='setup_grading_system'),
    
    # Transport Management (Missing URLs)
    path('transport/', views.transport_management, name='transport_management'),
    path('transport/routes/', views.transport_routes, name='transport_routes'),
    path('transport/vehicles/', views.transport_vehicles, name='transport_vehicles'),
    path('transport/assign/', views.assign_transport, name='assign_transport'),
    
    # Hostel Management (Missing URLs)
    path('hostel/', views.hostel_management, name='hostel_management'),
    path('hostel/rooms/', views.hostel_rooms, name='hostel_rooms'),
    path('hostel/allocations/', views.hostel_allocations, name='hostel_allocations'),
    path('hostel/allocate/', views.allocate_hostel, name='allocate_hostel'),
    
    # UI Elements
    path('ui/buttons/', views.buttons, name='buttons'),
    path('ui/modals/', views.modals, name='modals'),
    path('ui/alerts/', views.alerts, name='alerts'),
    path('ui/grid/', views.grid, name='grid'),
    path('ui/progress-bars/', views.progress_bars, name='progress_bars'),
    
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
    
    # AJAX/API Endpoints
    path('ajax/sections-by-class/<int:class_id>/', views.get_sections_by_class, name='get_sections_by_class'),
    path('ajax/check-username/', views.check_username_availability, name='check_username_availability'),
    path('ajax/check-email/', views.check_email_availability, name='check_email_availability'),
    path('ajax/get-students-by-class/<int:class_id>/', views.get_students_by_class, name='get_students_by_class'),
    path('ajax/get-subjects-by-class/<int:class_id>/', views.get_subjects_by_class, name='get_subjects_by_class'),
]