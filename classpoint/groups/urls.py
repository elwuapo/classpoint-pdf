from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path(
        "",
        view=views.GroupList.as_view(),
        name="list"
    ),
    path(
        "professor/",
        view=views.ProfessorGroupList.as_view(),
        name="professor_list"
    ),
    path(
        "<int:group_id>/add-students/",
        view=views.GroupManageStudents.as_view(),
        name="manage_students"
    ),
    path(
        "<int:group_id>/import-students/",
        view=views.GroupStudentsImport.as_view(),
        name="import_students"
    ),
    path(
        "create/",
        view=views.GroupCreate.as_view(),
        name="create"
    ),
    path(
        "edit/<int:group_id>/",
        view=views.GroupEdit.as_view(),
        name="edit"
    ),
    path(
        "details/<int:group_id>/",
        view=views.GroupDetail.as_view(),
        name="detail"
    ),
    path(
        "delete/<str:id>/",
        view=views.GroupDelete.as_view(),
        name="delete"
    ),
    path(
        "details/view-pdf/<int:group_id>/",
        view=views.GroupDetailViewPDF.as_view(),
        name="group_view_pdf"
    ),
]
