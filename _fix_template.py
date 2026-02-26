html = """\
{% extends 'base.html' %}
{% load static %}

{% block title %}{{ assignment.title }} - Assignment Details{% endblock %}

{% block extra_css %}
<style>
    :root {
        --primary-grad: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        --card-shadow: 0 10px 15px -3px rgba(0,0,0,.08), 0 4px 6px -2px rgba(0,0,0,.04);
    }
    .dashboard-content-one { background:#f8fafc; }
    .asgn-banner { border-radius:24px; overflow:hidden; box-shadow:var(--card-shadow); margin-bottom:30px; }
    .banner-header { background:var(--primary-grad); padding:36px; color:#fff; position:relative; }
    .banner-header h2 { font-weight:800; margin:0; letter-spacing:-.5px; }
    .banner-status-badge { position:absolute; top:24px; right:24px; padding:8px 18px; border-radius:100px; font-size:.8rem; font-weight:700; background:rgba(255,255,255,.2); color:#fff; }
    .banner-body { background:#fff; padding:30px; }
    .stat-pill { display:flex; flex-direction:column; align-items:center; background:#f8fafc; border-radius:16px; padding:20px 16px; }
    .stat-pill .value { font-size:2rem; font-weight:900; color:#1e293b; }
    .stat-pill .label { font-size:.7rem; font-weight:700; text-transform:uppercase; color:#94a3b8; letter-spacing:.5px; }
    .progress-track { height:10px; border-radius:100px; overflow:hidden; background:#e2e8f0; }
    .progress-fill { height:100%; border-radius:100px; }
    .submissions-card { background:#fff; border-radius:24px; padding:28px; box-shadow:var(--card-shadow); }
    .avatar-circle { width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:.95rem; flex-shrink:0; }
    .score-badge { padding:5px 12px; border-radius:100px; font-weight:700; font-size:.8rem; }
    .modal-content-luxe { border-radius:20px; border:none; overflow:hidden; }
    .modal-header-grade { background:var(--primary-grad); padding:24px 28px; }
    .modal-header-grade h5 { color:#fff; font-weight:800; margin:0; }
    .modal-body-grade { padding:28px; }
    .grade-form-label { font-weight:700; font-size:.88rem; color:#374151; margin-bottom:6px; display:block; }
    .grade-input { border-radius:12px; border:2px solid #e2e8f0; padding:11px 16px; font-size:.95rem; transition:border .25s; }
    .grade-input:focus { border-color:#6366f1; box-shadow:0 0 0 4px rgba(99,102,241,.1); outline:none; }
    .feedback-textarea { border-radius:12px; border:2px solid #e2e8f0; padding:12px 16px; resize:vertical; font-size:.9rem; transition:border .25s; }
    .feedback-textarea:focus { border-color:#6366f1; box-shadow:0 0 0 4px rgba(99,102,241,.1); outline:none; }
    .btn-grade-confirm { background:var(--primary-grad); border:none; border-radius:12px; padding:13px 28px; font-weight:800; color:#fff; width:100%; margin-top:12px; transition:all .25s; }
    .btn-grade-confirm:hover { box-shadow:0 6px 20px rgba(99,102,241,.35); }
    .submission-preview { background:#f8fafc; border-radius:12px; padding:16px; margin-bottom:16px; border:1px solid #e2e8f0; }
    .empty-sub { text-align:center; padding:60px; }
</style>
{% endblock %}

{% block content %}
<div id="wrapper" class="wrapper bg-ash">
    {% include 'includes/header.html' %}
    <div class="dashboard-page-one">
        {% include 'includes/sidebar.html' %}
        <div class="dashboard-content-one p-4">

            <div class="breadcrumbs-area mb-4">
                <h3>Assignment Details</h3>
                <ul>
                    <li><a href="{% url 'teacher_dashboard' %}">Dashboard</a></li>
                    <li><a href="{% url 'teacher_assignments' %}">Assignments</a></li>
                    <li>{{ assignment.title }}</li>
                </ul>
            </div>

            <div class="asgn-banner">
                <div class="banner-header">
                    <span class="banner-status-badge">{{ assignment.get_status_display }}</span>
                    <p class="mb-1" style="color:rgba(255,255,255,.7); font-size:.85rem; text-transform:uppercase; letter-spacing:.5px;">{{ assignment.subject.name }} &middot; {{ assignment.class_level.name }}</p>
                    <h2>{{ assignment.title }}</h2>
                    <p class="mt-2 mb-0" style="color:rgba(255,255,255,.8);">
                        <i class="fas fa-calendar-alt mr-2"></i>Due: {{ assignment.due_date|date:"l, d F Y" }}
                        {% if assignment.is_overdue %}<span class="badge badge-danger ml-2">Overdue</span>{% endif %}
                    </p>
                </div>
                <div class="banner-body">
                    <div class="row">
                        <div class="col-md-8">
                            {% if assignment.description %}
                            <h5 class="font-weight-bold mb-2">Instructions</h5>
                            <p class="text-muted" style="line-height:1.7;">{{ assignment.description|linebreaks }}</p>
                            {% endif %}
                            {% if assignment.attachment %}
                            <a href="{{ assignment.attachment.url }}" class="btn btn-outline-primary btn-sm rounded-pill" target="_blank"><i class="fas fa-download mr-2"></i>Download Attachment</a>
                            {% endif %}
                        </div>
                        <div class="col-md-4">
                            <div class="row">
                                <div class="col-4">
                                    <div class="stat-pill">
                                        <span class="value text-primary">{{ total_students }}</span>
                                        <span class="label">Total</span>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="stat-pill">
                                        <span class="value text-success">{{ submitted_count }}</span>
                                        <span class="label">Submitted</span>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="stat-pill">
                                        <span class="value text-warning">{{ graded_count }}</span>
                                        <span class="label">Graded</span>
                                    </div>
                                </div>
                            </div>
                            {% if total_students > 0 %}
                            <div class="mt-3">
                                <div class="d-flex justify-content-between mb-1">
                                    <small class="font-weight-bold text-muted">Submission Rate</small>
                                    <small class="font-weight-bold text-success">{% widthratio submitted_count total_students 100 %}%</small>
                                </div>
                                <div class="progress-track"><div class="progress-fill bg-success" style="width:{% widthratio submitted_count total_students 100 %}%;"></div></div>
                            </div>
                            {% if submitted_count > 0 %}
                            <div class="mt-3">
                                <div class="d-flex justify-content-between mb-1">
                                    <small class="font-weight-bold text-muted">Grading Progress</small>
                                    <small class="font-weight-bold text-primary">{% widthratio graded_count submitted_count 100 %}%</small>
                                </div>
                                <div class="progress-track"><div class="progress-fill bg-primary" style="width:{% widthratio graded_count submitted_count 100 %}%;"></div></div>
                            </div>
                            {% endif %}
                            {% endif %}
                        </div>
                    </div>
                    <div class="d-flex mt-4 flex-wrap" style="gap:10px;">
                        <a href="{% url 'assignment_edit' assignment.id %}" class="btn btn-outline-primary btn-sm rounded-pill px-4"><i class="fas fa-edit mr-2"></i>Edit</a>
                        {% if submitted_count > 0 %}
                        <a href="{% url 'assignment_download_submissions' assignment.id %}" class="btn btn-outline-success btn-sm rounded-pill px-4"><i class="fas fa-download mr-2"></i>Download All</a>
                        {% endif %}
                        <a href="{% url 'assignment_delete' assignment.id %}" class="btn btn-outline-danger btn-sm rounded-pill px-4"><i class="fas fa-trash mr-2"></i>Delete</a>
                    </div>
                </div>
            </div>

            <div class="submissions-card">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h4 class="font-weight-bold mb-0">Student Submissions <span class="badge badge-primary ml-2">{{ submissions.count }}</span></h4>
                    {% if submissions.count > 0 %}<span class="text-muted small">{{ graded_count }}/{{ submitted_count }} graded</span>{% endif %}
                </div>
                {% if submissions.exists %}
                <div class="table-responsive">
                    <table class="table" id="submissionsTable">
                        <thead>
                            <tr style="background:#f1f5f9;">
                                <th class="border-0" style="padding:14px 16px;">Student</th>
                                <th class="border-0">Submitted</th>
                                <th class="border-0">File</th>
                                <th class="border-0">Score</th>
                                <th class="border-0">Status</th>
                                <th class="border-0 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for submission in submissions %}
                            <tr>
                                <td style="vertical-align:middle;">
                                    <div class="d-flex align-items-center">
                                        {% if submission.student.photo %}
                                        <img src="{{ submission.student.photo.url }}" class="rounded-circle mr-2" width="40" height="40" alt="">
                                        {% else %}
                                        <div class="avatar-circle mr-2" style="background:#eef2ff; color:#6366f1;">{{ submission.student.first_name|first }}{{ submission.student.last_name|first }}</div>
                                        {% endif %}
                                        <div>
                                            <h6 class="mb-0 font-weight-bold">{{ submission.student.full_name }}</h6>
                                            <small class="text-muted">{{ submission.student.student_id }}</small>
                                        </div>
                                    </div>
                                </td>
                                <td style="vertical-align:middle;">
                                    {% if submission.submitted %}
                                    <span>{{ submission.submitted_at|date:"d M Y" }}</span>
                                    {% if submission.is_late %}<span class="badge badge-danger ml-1" style="font-size:.65rem;">Late</span>{% endif %}
                                    {% else %}
                                    <span class="text-muted">Not submitted</span>
                                    {% endif %}
                                </td>
                                <td style="vertical-align:middle;">
                                    {% if submission.submission_file %}
                                    <a href="{{ submission.submission_file.url }}" target="_blank" class="btn btn-outline-secondary btn-sm rounded-pill"><i class="fas fa-file mr-1"></i>View</a>
                                    {% elif submission.submission_text %}
                                    <span class="text-muted small"><i class="fas fa-align-left mr-1"></i>Text Only</span>
                                    {% else %}
                                    <span class="text-muted">&mdash;</span>
                                    {% endif %}
                                </td>
                                <td style="vertical-align:middle;">
                                    {% if submission.marks_obtained is not None %}
                                    <span class="font-weight-bold {% if submission.marks_obtained >= 80 %}text-success{% elif submission.marks_obtained >= 50 %}text-warning{% else %}text-danger{% endif %}">{{ submission.marks_obtained }}/{{ assignment.total_marks }}</span>
                                    {% else %}
                                    <span class="text-muted">&mdash;</span>
                                    {% endif %}
                                </td>
                                <td style="vertical-align:middle;">
                                    {% if submission.submitted %}
                                        {% if submission.marks_obtained is not None %}
                                        <span class="score-badge" style="background:#d1fae5; color:#065f46;">Graded</span>
                                        {% else %}
                                        <span class="score-badge" style="background:#fef3c7; color:#92400e;">Pending</span>
                                        {% endif %}
                                    {% else %}
                                    <span class="score-badge" style="background:#f3f4f6; color:#374151;">Not In</span>
                                    {% endif %}
                                </td>
                                <td style="vertical-align:middle; text-align:center;">
                                    {% if submission.submitted %}
                                    <button class="btn btn-primary btn-sm rounded-pill grade-btn"
                                            data-submission-id="{{ submission.id }}"
                                            data-student-name="{{ submission.student.full_name }}"
                                            data-student-id="{{ submission.student.student_id }}"
                                            data-current-marks="{{ submission.marks_obtained|default:'' }}"
                                            data-current-feedback="{{ submission.feedback|default:'' }}"
                                            data-submission-text="{{ submission.submission_text|default:'' }}"
                                            data-total-marks="{{ assignment.total_marks }}"
                                            data-toggle="modal"
                                            data-target="#gradeModal">
                                        <i class="fas fa-edit mr-1"></i>{% if submission.marks_obtained is not None %}Update{% else %}Grade{% endif %}
                                    </button>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="empty-sub">
                    <i class="fas fa-inbox fa-4x mb-4" style="color:#c7d2fe;"></i>
                    <h5 class="font-weight-bold text-muted">No submissions yet</h5>
                    <p class="text-muted">{% if total_students > 0 %}Students have not submitted any work yet.{% else %}No students are enrolled in this class.{% endif %}</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Grade Modal -->
<div class="modal fade" id="gradeModal" tabindex="-1" role="dialog" aria-labelledby="gradeModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content modal-content-luxe">
            <div class="modal-header-grade">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 id="gradeModalLabel">Grade Submission</h5>
                        <p class="mb-0" style="color:rgba(255,255,255,.75); font-size:.85rem;" id="grade-student-label"></p>
                    </div>
                    <button type="button" class="close text-white" data-dismiss="modal" style="opacity:.7; font-size:1.5rem;"><span>&times;</span></button>
                </div>
            </div>
            <div class="modal-body-grade">
                <div class="submission-preview" id="submission-text-preview" style="display:none;">
                    <p class="small font-weight-bold text-muted mb-1">Student Written Response:</p>
                    <p id="preview-submission-text" class="mb-0"></p>
                </div>
                <form id="gradeForm" method="POST">
                    {% csrf_token %}
                    <div class="mb-4">
                        <label class="grade-form-label">Score <span class="text-muted font-weight-normal" id="totalMarksHint">/ 100</span></label>
                        <input type="number" name="marks" id="marksInput" class="form-control grade-input" min="0" step="0.5" placeholder="Enter score">
                        <div id="marksFeedback" class="mt-2" style="font-size:.82rem; font-weight:700; display:none;"></div>
                    </div>
                    <div class="mb-4">
                        <label class="grade-form-label">Feedback <span class="text-muted font-weight-normal">(Optional)</span></label>
                        <textarea name="feedback" id="feedbackInput" class="form-control feedback-textarea" rows="4" placeholder="Write your feedback..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-grade-confirm" id="submitGradeBtn"><i class="fas fa-save mr-2"></i>Save Grade</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('.grade-btn').on('click', function() {
        var subId = $(this).data('submission-id');
        var studentName = $(this).data('student-name');
        var studentId = $(this).data('student-id');
        var currMarks = $(this).data('current-marks');
        var currFeedback = $(this).data('current-feedback');
        var subText = $(this).data('submission-text');
        var totalMarks = $(this).data('total-marks');
        $('#grade-student-label').text(studentName + ' - ' + studentId);
        $('#totalMarksHint').text('/ ' + totalMarks);
        $('#marksInput').val(currMarks !== '' ? currMarks : '');
        $('#marksInput').attr('max', totalMarks);
        $('#feedbackInput').val(currFeedback);
        $('#marksFeedback').hide();
        if (subText && subText.trim()) {
            $('#preview-submission-text').text(subText);
            $('#submission-text-preview').show();
        } else {
            $('#submission-text-preview').hide();
        }
        $('#gradeForm').attr('action', '/dashboard/teacher/grade-submission/' + subId + '/');
    });

    $('#marksInput').on('input', function() {
        var val = parseFloat($(this).val());
        var total = parseFloat($(this).attr('max'));
        var fb = $('#marksFeedback');
        if (isNaN(val) || !$(this).val()) { fb.hide(); return; }
        var pct = (val / total) * 100;
        var color, msg;
        if (pct >= 80) { color='#059669'; msg='Excellent! (' + pct.toFixed(0) + '%)'; }
        else if (pct >= 60) { color='#2563eb'; msg='Good (' + pct.toFixed(0) + '%)'; }
        else if (pct >= 40) { color='#d97706'; msg='Average (' + pct.toFixed(0) + '%)'; }
        else { color='#dc2626'; msg='Below Pass (' + pct.toFixed(0) + '%)'; }
        fb.css('color', color).text(msg).show();
    });

    $('#gradeForm').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var btn = $('#submitGradeBtn');
        btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-2"></i>Saving...');
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize(),
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function(data) {
                if (data.success) {
                    $('#gradeModal').modal('hide');
                    setTimeout(function() { location.reload(); }, 800);
                } else {
                    alert(data.message || 'Error saving grade.');
                }
            },
            error: function() { alert('Network error. Please try again.'); },
            complete: function() { btn.prop('disabled', false).html('<i class="fas fa-save mr-2"></i>Save Grade'); }
        });
    });
});
</script>
{% endblock %}
"""

with open(r"templates\teachers\assignment_detail.html", "w", encoding="utf-8", newline="\n") as f:
    f.write(html)

print("Written OK. Verifying widthratio lines:")
for i, line in enumerate(html.split("\n"), 1):
    if "widthratio" in line:
        print(f"  L{i}: {line.strip()}")
