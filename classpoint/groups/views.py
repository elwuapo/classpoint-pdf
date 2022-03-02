from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    UpdateView
)

from braces.views import (
    LoginRequiredMixin,
    StaticContextMixin,
)

from ..base.generic_views import (
    DataTablesView,
    DirectDeleteView,
    UserPassesTestRedirectMixin
)
from ..students.forms import StudentFormSet

from .forms import GroupForm, GroupStudentsImportForm
from .models import Group

from xhtml2pdf import pisa


class GroupBaseMixin(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
):
    static_context = {
        'section': 'groups'
    }

    def test_func(self, user):
        return (
            user.is_coordinator or
            user.is_general_coordinator
        )


class GroupDetail(
    GroupBaseMixin,
    DetailView
):
    context_object_name = 'group'
    model = Group
    pk_url_kwarg = "group_id"
    template_name = 'groups/group_detail.html'

    def test_func(self, user):
        return (
            user.is_coordinator or
            user.is_general_coordinator or
            user.is_professor
        )

    def get_queryset(self):
        return Group.objects.filter(
            school=self.request.user.school
        ).select_related(
            'school'
        )


class GroupList(
    GroupBaseMixin,
    DataTablesView
):
    ajax_template_name = 'groups/groups.json'

    column_index_map = {
        0: 'name',
        1: 'group_type',
        2: 'responsible_professor__first_name',
        3: 'id',
        4: 'id',
        5: 'student_count',
        6: 'id',
        7: 'id',
        8: 'id',
    }

    template_name = 'groups/group_list.html'

    def get_items(self):
        return Group.objects.filter(
            school=self.request.user.school,
            active=True,
        ).annotate(
            student_count=Count('students')
        ).select_related(
            'responsible_professor'
        ).prefetch_related(
            'evaluations__evaluation__activity__learning_target'
        )


class ProfessorGroupList(
    GroupBaseMixin,
    DataTablesView
):
    ajax_template_name = 'groups/professor_groups.json'

    column_index_map = {
        0: 'name',
        1: 'group_type',
        2: 'student_count',
        3: 'id',
        4: 'id',
        5: 'id',
        6: 'id',
    }

    template_name = 'groups/professor_group_list.html'

    def test_func(self, user):
        return user.is_professor

    def get_items(self):
        return Group.objects.filter(
            school=self.request.user.school,
            responsible_professor=self.request.user,
            active=True,
        ).annotate(
            student_count=Count('students')
        ).select_related(
            'responsible_professor'
        ).prefetch_related(
            'evaluations__evaluation__activity__learning_target'
        )


class GroupCreate(
    GroupBaseMixin,
    CreateView,
):
    form_class = GroupForm
    template_name = 'groups/group_create.html'

    def get_success_url(self):
        return reverse(
            'groups:list'
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.request.user.school
        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.user.school

        result = super().form_valid(form)

        return result


class GroupEdit(
    GroupBaseMixin,
    UpdateView
):
    form_class = GroupForm
    pk_url_kwarg = 'group_id'
    template_name = 'groups/group_edit.html'

    def get_queryset(self):
        return Group.objects.filter(
            school=self.request.user.school
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.request.user.school
        return kwargs

    def get_success_url(self):
        return reverse(
            'groups:list'
        )


class GroupStudentsImport(
    GroupBaseMixin,
    FormView
):
    form_class = GroupStudentsImportForm
    template_name = 'groups/group_import.html'

    def get_success_url(self):
        return reverse(
            'groups:list'
        )

    @cached_property
    def group(self):
        return Group.objects.get(
            pk=self.kwargs.get('group_id')
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['group'] = self.group
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['group'] = self.group
        return form_kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class GroupManageStudents(
    GroupBaseMixin,
    UpdateView,
):
    form_class = StudentFormSet
    pk_url_kwarg = 'group_id'
    template_name = 'groups/manage_students.html'

    def get_queryset(self):
        return Group.objects.filter(
            school=self.request.user.school
        )

    def get_group(self):
        return get_object_or_404(
            Group,
            id=self.kwargs[self.pk_url_kwarg]
        )

    def get(self, request, *_, **__):
        group = self.get_group()
        invite_formset = self.get_formset(
            group
        )

        return self.render_to_response({
            'formset': invite_formset,
            'group': group,
            'section': 'groups',
        })

    def post(self, request, *_, **__):
        group = self.get_group()

        formset = self.get_formset(
            group,
            request.POST
        )

        ruts = set()

        for form in formset.forms:
            if form.is_valid():
                user_rut = form.cleaned_data.get('rut')

                if user_rut in ruts:
                    formset.errors.append(
                        f'Ya existe otro alumno en esta lista con el RUT {user_rut}'
                    )
                else:
                    ruts.add(user_rut)

        if formset.is_valid():
            for form in formset.forms:
                student = form.instance
                student.group = group

            formset.save()

            return redirect('groups:list')

        return self.render_to_response({
            'formset': formset,
            'group': group,
            'section': 'groups',
        })

    def get_formset(self, instance, data=None):
        return self.form_class(
            instance=instance,
            data=data,
            form_kwargs={
                'user': self.request.user,
            }
        )


class GroupDelete(
    DirectDeleteView,
):
    def test_func(self, user):
        return user.is_coordinator

    def get_queryset(self):
        return Group.objects.filter(
            school=self.request.user.school
        )

    def get_success_url(self):
        return reverse(
            "groups:list",
        )

class PDFViewRenderMixin(object):
    @staticmethod
    def render_pdf(template_name, context, filename):
        template = get_template(template_name)

        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename={}'.format(filename)

        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            link_callback=None
        )

        return pisa_status, response, html

class GroupDetailViewPDF(PDFViewRenderMixin, View):
    template_name = 'groups/group_detail_print.html'

    def get(self, request, group_id):
        group = Group.objects.get(id = group_id)
        
        pisa_status, response, html = self.render_pdf(
            self.template_name,
            {
                'title': 'listado de alumnos',
                'group': group,
            },
            'listado_de_alumnos_{}'.format(group)
        )

        profesor = group.responsible_professor

        if pisa_status.err:
            return HttpResponse(f'We had some errors <pre>{html}</pre>')

        return response

