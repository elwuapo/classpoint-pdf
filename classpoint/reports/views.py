from io import BytesIO
from datetime import date as dt

from braces.views import (
    LoginRequiredMixin,
    StaticContextMixin
)

from django.http.response import HttpResponse
from django.template.loader import get_template
from django.views.generic import TemplateView
from django.views import View

from classpoint.reports.utils import generate_bar_and_line_char, generate_bar_chart, generate_pie_chart
from classpoint.schools.models import School

from ..base.generic_views import UserPassesTestRedirectMixin
from ..groups.models import Group
from ..learning_targets.models import LearningTarget
from ..students.models import Student

from .forms import (
    CourseByCoreForm,
    StudentByCoreForm,
    StudentByTargetForm
)

from xhtml2pdf import pisa

class ReportBaseMixin(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
):
    static_context = {
        'section': 'reports'
    }

    def test_func(self, user):
        return (
            user.is_coordinator or
            user.is_professor or
            user.is_admin or
            user.is_general_coordinator
        )


class ReportList(
    ReportBaseMixin,
    TemplateView,
):
    template_name = 'reports/report_index.html'


class StudentByTarget(
    ReportBaseMixin,
    TemplateView,
):
    form_class = StudentByTargetForm
    template_name = 'reports/student_by_target.html'

    def get_form_data(self):
        form_data = self.request.GET.copy()

        school = (
            form_data.get('group') or
            self.request.user.school
        )

        if 'level' not in form_data:
            form_data['level'] = Group.KINDER

        if 'core' not in form_data:
            form_data['core'] = LearningTarget.VERBAL_LANGUAGE

        if 'group' not in form_data:
            if 'student_id' not in self.request.GET:
                level = self.request.GET.get(
                    'level',
                    Group.KINDER,
                )

                first_group = Group.objects.filter(
                    school=school,
                    group_type=level,
                ).first()
            else:
                first_group = Student.objects.filter(
                    pk=self.request.GET['student_id'],
                    group__school=school,
                ).first().group

            form_data['group'] = first_group

        if 'school' not in form_data:
            form_data['school'] = self.request.user.school.pk

        return form_data

    def get_form_kwargs(self):
        return {
            'user': self.request.user,
            'level': self.request.GET.get(
                'level',
                Group.KINDER,
            ),
            'core': self.request.GET.get(
                'core',
                LearningTarget.VERBAL_LANGUAGE,
            )
        }

    def get_form(self):
        form = self.form_class(
            self.get_form_data(),
            **self.get_form_kwargs(),
        )
        return form

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = self.get_form()
        form.is_valid()

        context_data['form'] = form
        context_data['list_students'] = False

        if 'student_id' in self.request.GET:
            student = Student.objects.filter(
                pk=self.request.GET['student_id'],
                group__school=self.request.user.school,
            ).first()

            learning_target = self.request.GET.get(
                'learning_target'
            )

            context_data['student'] = student

            student_by_core_data, student_evaluations = form.get_report_data(
                student=student,
                learning_target=learning_target
            )

            context_data['student_by_core_data'] = student_by_core_data
            context_data['student_evaluations'] = student_evaluations

            context_data['core_name'] = student_by_core_data[0]['core_name']

            if learning_target:
                learning_target = LearningTarget.objects.get(pk=learning_target)
                context_data['learning_target_pretty_name'] = learning_target.abbreviated_name
            else:
                context_data['learning_target_pretty_name'] = student_by_core_data[0]['core_abbreviation']

        context_data['students'] = form.get_students().only(
            'pk',
            'first_name',
            'last_name',
            'list_number',
        )
        context_data['list_students'] = True

        context_data['request'] = self.request
        context_data['report'] = 'report_by_objective'

        return context_data


class CourseByCore(
    ReportBaseMixin,
    TemplateView,
):
    form_class = CourseByCoreForm
    template_name = 'reports/course_by_core.html'

    def get_form_data(self):
        form_data = self.request.GET.copy()
        
        if 'level' not in form_data:
            form_data['level'] = Group.KINDER

        if 'core' not in form_data:
            form_data['core'] = LearningTarget.VERBAL_LANGUAGE

        school = (
            form_data.get('group') or
            self.request.user.school
        )

        if 'group' not in form_data:
            if 'student_id' not in self.request.GET:
                level = self.request.GET.get(
                    'level',
                    Group.KINDER,
                )

                first_group = Group.objects.filter(
                    school=school,
                    group_type=level,
                ).first()
            else:
                first_group = Student.objects.filter(
                    pk=self.request.GET['student_id'],
                    group__school=school,
                ).first().group

            form_data['group'] = first_group

        if 'school' not in form_data:
            form_data['school'] = self.request.user.school.pk

        return form_data

    def get_form(self):
        return self.form_class(
            self.get_form_data(),
            **self.get_form_kwargs(),
        )

    def get_form_kwargs(self):
        return {
            'user': self.request.user,
            'level': self.request.GET.get(
                'level',
                Group.KINDER,
            ),
            'core': self.request.GET.get(
                'core',
                LearningTarget.VERBAL_LANGUAGE,
            )
        }

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = self.get_form()
        form.is_valid()

        context_data['form'] = form
        context_data['course'] = form.cleaned_data.get(
            'course',
        ) or form.fields['course'].queryset.first()

        course_by_core_data = form.get_report_data(
            course=context_data['course'],
            core=form.cleaned_data['core'],
            learning_target=form.cleaned_data.get(
                'learning_target'
            ),
        )

        context_data['course_by_core_data'] = course_by_core_data

        context_data['core_name'] = course_by_core_data and course_by_core_data[-1]['core_name']

        return context_data


class StudentByCore(
    StudentByTarget
):
    template_name = 'reports/student_by_core.html'
    form_class = StudentByCoreForm

    def get_context_data(self, **kwargs):
        context_data = super(TemplateView, self).get_context_data(**kwargs)

        form = self.get_form()
        form.is_valid()

        context_data['form'] = form
        context_data['list_students'] = False

        if 'student_id' in self.request.GET:
            student = Student.objects.filter(
                pk=self.request.GET['student_id'],
                group__school=self.request.user.school,
            ).first()

            learning_target = self.request.GET.get(
                'learning_target'
            )

            context_data['student'] = student

            student_by_core_data = form.get_report_data(
                student=student,
                learning_target=learning_target
            )

            context_data['student_entry'] = student_by_core_data

        context_data['students'] = form.get_students().only(
            'pk',
            'first_name',
            'last_name',
            'list_number',
        )
        context_data['list_students'] = True

        context_data['request'] = self.request
        context_data['report'] = 'report_by_core'

        return context_data


class StudentByTargetPDF(View):
    def link_callback(self, uri, rel):
        pass

    def get(self, request, *args, **kwargs):
        student = Student.objects.get(id = request.GET.get('student_id', ''))
        school = School.objects.get(id = request.GET.get('school', ''))
        learning = request.GET.get('learning_target', '')
        grade = student.group
        fullname = student.full_name
        template = get_template('reports/report_pdf_student_by_target.html')
        level = ''
        core = ''

        if(learning == '' or learning == 'None'):
            objectives  = LearningTarget.objects.filter(core = request.GET.get('core', '')).filter(level = request.GET.get('level', '')).order_by('identifier')
        else:
            objectives  = LearningTarget.objects.filter(id = request.GET.get('learning_target', '')).order_by('identifier')

        for id, level in grade.GROUP_TYPE_CHOICES:
            if(id == int(request.GET.get('level', ''))):
                level = level
                break

        for id, core in LearningTarget.CORE_CHOICES:
            if(id == int(request.GET.get('core', ''))):
                core = core
                break
        
        bar_chart_data = request.GET.get('bar_chart', '')
        line_chart_data = request.GET.get('line_chart', '')

        # [(student, student_avg), ('group', 'group_avg')]
        data1 = eval(bar_chart_data)

        # [(date, evaluation, group_evaluation), ...]
        data2 = eval(line_chart_data)

        chart = generate_bar_and_line_char(data1, data2)

        context = {
            'title': '{}.pdf'.format(fullname),
            'name': fullname,
            'date': dt.today().strftime("%d/%m/%Y"),
            'institute': school.name,
            'core': core,               # Lenguaje Verbal (no llega mediante el GET)
            'level': level,             # Kinder
            'objectives': objectives,   # Todos, 1-Expresar oralmente, 2-Comprender en base a textos orales.
            'grade': grade.name,        # Kinder A
            'chart': '{}://{}{}{}'.format(request.scheme, request.headers['Host'], '/static/', chart)
        }
        
        html = template.render(context)

        response = HttpResponse(content_type = 'application/pdf')
        response['Content-Disposition'] = 'filename="{}.pdf"'.format(fullname)
        
        pisaStatus = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=response, link_callback=None)

        if(pisaStatus.err):
            return HttpResponse('We had some erros <pre>' + html + '</pre>')
        else:
            return response

class StudentByCorePDF(View):
    def get(self, request, *args, **kwargs):
        student = Student.objects.get(id = request.GET.get('student_id', ''))
        school = School.objects.get(id = request.GET.get('school', ''))
        grade = student.group
        fullname = student.full_name
        template = get_template('reports/report_pdf_student_by_core.html')
        level = ''
        core = ''

        for id, level in grade.GROUP_TYPE_CHOICES:
            if(id == int(request.GET.get('level', ''))):
                level = level
                break

        for id, core in LearningTarget.CORE_CHOICES:
            if(id == int(request.GET.get('core', ''))):
                core = core
                break

        bar_chart_data  = request.GET.get('bar_chart', '')
        
        data = eval(bar_chart_data)

        bar_chart = generate_bar_chart(data)
        pie_chart = generate_pie_chart(data)
        
        context = {
            'title': '{}.pdf'.format(fullname),
            'name': fullname,
            'date': dt.today().strftime("%d/%m/%Y"),
            'institute': school.name,
            'core': core,               # Lenguaje Verbal (no llega mediante el GET)
            'level': level,             # Kinder
            'grade': grade.name,        # Kinder A
            'bar_chart': '{}://{}{}{}'.format(request.scheme, request.headers['Host'], '/static/', bar_chart),
            'pie_chart': '{}://{}{}{}'.format(request.scheme, request.headers['Host'], '/static/', pie_chart),
        }

        html = template.render(context)

        response = HttpResponse(content_type = 'application/pdf')
        response['Content-Disposition'] = 'filename="{}.pdf"'.format(fullname)
        
        pisaStatus = pisa.CreatePDF(
            BytesIO(html.encode('UTF-8')), 
            dest=response, 
            link_callback=None
        )

        if(pisaStatus.err):
            return HttpResponse('We had some erros <pre>' + html + '</pre>')
        else:
            return response