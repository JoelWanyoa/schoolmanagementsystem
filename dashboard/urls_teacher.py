from django.urls import path
from . import views
from core.decorators import teacher_required

urlpatterns = [
    path('', teacher_required(views.teacher_dashboard), name='teacher_dashboard'),

    # Teacher Dashboard
    path('teacher/my-classes/', teacher_required(views.teacher_my_classes), name='teacher_my_classes'),
    path('teacher/class-schedule/', teacher_required(views.teacher_class_schedule), name='teacher_class_schedule'),
    path('teacher/my-students/', teacher_required(views.teacher_my_students), name='teacher_my_students'),
    path('teacher/attendance/', teacher_required(views.teacher_attendance), name='teacher_attendance'),
    path('teacher/subjects/', teacher_required(views.teacher_subjects), name='teacher_subjects'),
    path('teacher/assignments/', teacher_required(views.teacher_assignments), name='teacher_assignments'),
    path('teacher/exam-results/', teacher_required(views.teacher_exam_results), name='teacher_exam_results'),

    # Assignments
    path('teacher/assignments/create/', teacher_required(views.assignment_create), name='assignment_create'),
    path('teacher/assignments/<int:assignment_id>/', teacher_required(views.assignment_detail), name='assignment_detail'),
    path('teacher/assignments/<int:assignment_id>/edit/', teacher_required(views.assignment_edit), name='assignment_edit'),
    path('teacher/assignments/<int:assignment_id>/delete/', teacher_required(views.assignment_delete), name='assignment_delete'),
    path('teacher/assignments/<int:assignment_id>/download-submissions/', teacher_required(views.assignment_download_submissions), name='assignment_download_submissions'),

    # AJAX endpoints
    path('teacher/mark-attendance/', teacher_required(views.mark_attendance), name='mark_attendance'),
    path('teacher/get-class-students/<int:class_id>/', teacher_required(views.get_class_students), name='get_class_students'),

    # Exam Management
    path('teacher/exams/', teacher_required(views.teacher_exam_management), name='teacher_exam_management'),
    path('teacher/exams/create/', teacher_required(views.create_exam), name='create_exam'),
    path('teacher/exams/<int:exam_id>/edit/', teacher_required(views.edit_exam), name='edit_exam'),
    path('teacher/exams/<int:exam_id>/delete/', teacher_required(views.delete_exam), name='delete_exam'),
    path('teacher/exams/<int:exam_id>/enter-marks/', teacher_required(views.enter_marks), name='enter_marks'),
    path('teacher/exams/<int:exam_id>/results/', teacher_required(views.exam_results), name='exam_results'),
    path('teacher/exams/<int:exam_id>/analysis/', teacher_required(views.exam_analysis), name='exam_analysis'),
    path('teacher/exams/<int:exam_id>/export-excel/', teacher_required(views.export_results_excel), name='export_results_excel'),
    path('teacher/exams/<int:exam_id>/export-pdf/', teacher_required(views.export_results_pdf), name='export_results_pdf'),
    path('teacher/exams/<int:exam_id>/bulk-upload/', teacher_required(views.bulk_upload_results), name='bulk_upload_results'),

    # Results
    path('teacher/subject-results/', teacher_required(views.subject_results), name='subject_results'),
    path('teacher/subject-results/<int:subject_id>/', teacher_required(views.subject_results), name='subject_results_detail'),
    path('teacher/class-results/', teacher_required(views.class_results), name='class_results'),
    path('teacher/class-results/<int:class_id>/', teacher_required(views.class_results), name='class_results_detail'),
    path('teacher/report-card/<int:student_id>/', teacher_required(views.generate_report_card), name='generate_report_card'),
    path('teacher/report-card/<int:student_id>/<str:term>/', teacher_required(views.generate_report_card), name='generate_report_card_term'),
]
