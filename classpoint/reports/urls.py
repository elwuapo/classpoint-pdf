from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path(
        "",
        view=views.ReportList.as_view(),
        name="index"
    ),
    path(
        "student-by-target/",
        view=views.StudentByTarget.as_view(),
        name="student_by_target"
    ),
    path(
        "course-by-core/",
        view=views.CourseByCore.as_view(),
        name="course_by_core"
    ),
    path(
        "student-by-core/",
        view=views.StudentByCore.as_view(),
        name="student_by_core"
    ),
    path(
        "student-by-target/download-pdf/",
        view=views.StudentByTargetPDF.as_view(),
        name="student-by-target-download-pdf"
    ),
    path(
        "student-by-core/download-pdf/",
        view=views.StudentByCorePDF.as_view(),
        name="student-by-core-download-pdf"
    ),
]
