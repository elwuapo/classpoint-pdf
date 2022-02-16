from io import BytesIO
from django.db.models import Count, Q
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView
)

from braces.views import (
    LoginRequiredMixin,
    StaticContextMixin,
)

from classpoint.evaluations.utils import generate_pie_and_bar_charts

from ..base.generic_views import (
    DataTablesView,
    DirectDeleteView,
    UserPassesTestRedirectMixin
)
from ..groups.models import Group
from ..learning_targets.models import Activity
from ..students.models import Student

from .forms import (
    CoordinatorAnecdotalRecordForm,
    GeneralEvaluationForm,
    GroupEvaluationForm,
    ProfessorAnecdotalRecordForm,
    StudentEvaluationFormset,
)
from .models import (
    AnecdotalRecord,
    GeneralEvaluation,
    GroupEvaluation,
    StudentEvaluation,
    StudentEvaluationChange
)

from xhtml2pdf import pisa


class EvaluationBaseMixin(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
):
    static_context = {
        'section': 'evaluations'
    }

    def test_func(self, user):
        return (
            user.is_coordinator or
            user.is_general_coordinator
        )


class GroupEvaluationMixin(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
):
    static_context = {
        'section': 'evaluations'
    }

    def test_func(self, user):
        return user.is_professor


class AnecdotalRecordMixin(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
):
    static_context = {
        'section': 'anecdotal_records'
    }

    def test_func(self, user):
        return (
            user.is_professor or
            user.is_coordinator or
            user.is_general_coordinator
        )

    @staticmethod
    def get_records(user):
        anecdotal_records = AnecdotalRecord.objects.filter(
            student__group__school=user.school,
            active=True,
        ).select_related(
            'student',
        )

        if user.is_professor:
            assigned_groups = user.assigned_groups.all()
            anecdotal_records = anecdotal_records.filter(
                student__group__in=assigned_groups
            )

        return anecdotal_records

    @staticmethod
    def get_students_with_anecdotal_record(user):
        students = Student.objects.filter(
            group__school=user.school,
        ).select_related(
            'group'
        ).annotate(
            anecdotal_record_count=Count(
                'anecdotal_records',
                filter=Q(active=True)
            )
        ).filter(
            anecdotal_record_count__gte=1
        )

        if user.is_professor:
            assigned_groups = user.assigned_groups.all()
            students = students.filter(
                group__in=assigned_groups
            )

        return students


class EvaluationDetail(
    EvaluationBaseMixin,
    DetailView
):
    context_object_name = 'evaluation'
    model = GeneralEvaluation
    pk_url_kwarg = "evaluation_id"
    template_name = 'evaluations/evaluation_detail.html'

    def get_queryset(self):
        return GeneralEvaluation.objects.filter(
            school=self.request.user.school
        ).prefetch_related(
            'group_evaluations'
        )


class EvaluationDelete(
    DirectDeleteView,
):
    def test_func(self, user):
        return (
            user.is_admin or
            user.is_coordinator or
            user.is_general_coordinator
        )

    def get_queryset(self):
        return GeneralEvaluation.objects.filter(
            school=self.request.user.school
        )

    def get_success_url(self):
        return reverse(
            "evaluations:list",
        )


class GroupEvaluationDelete(
    DirectDeleteView,
):
    pk_url_kwarg = 'group_evaluation_id'

    def test_func(self, user):
        return user.is_professor

    def get_queryset(self):
        return GroupEvaluation.objects.filter(
            group__in=self.request.user.assigned_groups.all()
        )

    def get_success_url(self):
        return reverse(
            "evaluations:group_evaluations_list",
        )


class EvaluationView(
    LoginRequiredMixin,
    UserPassesTestRedirectMixin,
    StaticContextMixin,
    DetailView,
):
    context_object_name = 'group_evaluation'
    pk_url_kwarg = 'evaluation_id'
    static_context = {
        'section': 'evaluations'
    }

    template_name = 'evaluations/evaluation_view.html'

    def test_func(self, user):
        return (
            user.is_admin or
            user.is_coordinator or
            user.is_general_coordinator or
            user.is_professor
        )

    def get_queryset(self):
        user = self.request.user

        if user.is_coordinator or user.is_general_coordinator:
            return GroupEvaluation.objects.filter(
                group__school=self.request.user.school
            )

        return GroupEvaluation.objects.filter(
            group__in=user.assigned_groups.all()
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        group_evaluation = context_data[self.context_object_name]
        activity = group_evaluation.evaluation.activity

        context_data['beginning'] = (
            group_evaluation.override_beginning or
            activity.learning_experience_beginning
        )

        context_data['original_beginning'] = activity.learning_experience_beginning

        context_data['development'] = (
            group_evaluation.override_development or
            activity.learning_experience_development
        )

        context_data['original_development'] = activity.learning_experience_development

        context_data['conclusion'] = (
            group_evaluation.override_conclusion or
            activity.learning_experience_conclusion
        )

        context_data['original_conclusion'] = activity.learning_experience_conclusion

        context_data['identity_and_autonomy_target'] = (
            group_evaluation.override_identity_and_autonomy_target or
            activity.identity_and_autonomy_target
        )

        context_data['coexistence_and_citizenship_target'] = (
            group_evaluation.override_coexistence_and_citizenship_target or
            activity.coexistence_and_citizenship_target
        )

        context_data['corporality_and_movement_target'] = (
            group_evaluation.override_corporality_and_movement_target or
            activity.corporality_and_movement_target
        )

        context_data['materials'] = (
            group_evaluation.override_materials or
            activity.materials
        )

        original_activity_values = {
            'original_identity_and_autonomy_target': activity.identity_and_autonomy_target,
            'original_coexistence_and_citizenship_target': activity.coexistence_and_citizenship_target,
            'original_corporality_and_movement_target': activity.corporality_and_movement_target,
            'original_materials': activity.materials,
        }

        context_data.update(original_activity_values)

        return context_data


class EvaluationList(
    EvaluationBaseMixin,
    DataTablesView
):
    ajax_template_name = 'evaluations/evaluations.json'

    column_index_map = {
        0: 'activity__activity_id',
        1: 'activity__learning_target__name',
        2: 'activity__learning_target__level',
        3: 'due_date',
        4: 'group_count',
    }

    template_name = 'evaluations/evaluation_list.html'

    def get_items(self):
        return GeneralEvaluation.objects.filter(
            school=self.request.user.school,
            active=True,
        ).select_related(
            'activity',
            'activity__learning_target',
        ).prefetch_related(
            'group_evaluations__group',
        ).annotate(
            group_count=Count('group_evaluations')
        )


class EvaluationCreate(
    EvaluationBaseMixin,
    CreateView,
):
    form_class = GeneralEvaluationForm
    template_name = 'evaluations/evaluation_create.html'
    activity_url_pkwarg = 'activity_id'
    level_types = {
        'infant_nursery': Group.SALA_CUNA_MENOR,
        'toddler_nursery': Group.SALA_CUNA_MAYOR,
        'kinder': Group.KINDER,
        'pre_kinder': Group.PRE_KINDER,
        'lower_medium': Group.MEDIO_MENOR,
        'upper_medium': Group.MEDIO_MAYOR,
    }

    def test_func(self, user):
        return (
            user.is_coordinator or
            user.is_general_coordinator or
            user.is_professor
        )

    def get_activity(self):
        activity_id = self.kwargs.get(self.activity_url_pkwarg)

        return Activity.objects.filter(
            id=activity_id,
        ).first()

    def get_success_url(self):
        if self.request.user.is_professor:
            return reverse(
                'evaluations:group_evaluations_list'
            )

        return reverse(
            'evaluations:list'
        )

    @staticmethod
    def get_activities():
        return Activity.objects.select_related(
            'learning_target',
        )

    def get_initial(self):
        return {
            'due_date': timezone.now().date() + timezone.timedelta(days=30),
            'activity': self.get_activities().filter(
                pk=self.kwargs.get('activity_id')
            ).first()
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.request.user.school

        level = None

        activity_id = self.kwargs.get('activity_id')

        if activity_id:
            target_activity = self.get_activities().filter(
                pk=activity_id
            ).first()

            if target_activity:
                level = target_activity.learning_target.level
        else:
            level = self.level_types.get(
                self.request.GET.get(
                    'type',
                )
            )

        kwargs['level'] = level
        kwargs['user'] = self.request.user

        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.user.school
        form.instance.activity = form.cleaned_data['activity']

        result = super().form_valid(form)

        evaluation = form.instance
        groups = form.cleaned_data['selected_groups']
        student_evaluations = []

        for group in groups:
            group_evaluation = GroupEvaluation.objects.create(
                group=group,
                evaluation=evaluation,
            )

            for student in group.students.all():
                student_evaluations.append(
                    StudentEvaluation(
                        group_evaluation=group_evaluation,
                        student=student,
                    )
                )

        StudentEvaluation.objects.bulk_create(
            student_evaluations
        )

        return result


class EvaluationEdit(
    EvaluationBaseMixin,
    UpdateView
):
    form_class = GeneralEvaluationForm
    pk_url_kwarg = 'evaluation_id'
    template_name = 'evaluations/evaluation_edit.html'

    def get_queryset(self):
        return GeneralEvaluation.objects.filter(
            school=self.request.user.school
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['school'] = self.request.user.school
        return kwargs

    def get_initial(self):
        evaluation = self.object
        groups = [
            group_evaluation.group
            for group_evaluation
            in evaluation.group_evaluations.select_related(
                'group'
            )
        ]

        initial = super().get_initial()
        initial['selected_groups'] = groups

        return initial

    def form_valid(self, form):
        general_evaluation = form.instance

        group_ids = set(
            general_evaluation.group_evaluations.values_list(
                'group_id',
                flat=True
            )
        )

        evaluations = general_evaluation.group_evaluations.all()

        result = super().form_valid(form)

        selected_groups_ids = {
            group.id
            for group
            in form.cleaned_data['selected_groups']
        }

        to_add_group_ids = selected_groups_ids - group_ids

        student_evaluations = []

        for group_id in to_add_group_ids:
            group_evaluation, _ = GroupEvaluation.objects.get_or_create(
                group_id=group_id,
                evaluation=general_evaluation,
            )

            for student in Student.objects.filter(
                group_id=group_id
            ):
                student_evaluations.append(
                    StudentEvaluation(
                        group_evaluation=group_evaluation,
                        student=student,
                    )
                )

        to_delete_group_ids = group_ids - selected_groups_ids

        to_update_group_ids = group_ids & selected_groups_ids

        for group_id in to_update_group_ids:
            group_evaluation, _ = evaluations.get_or_create(
                group_id=group_id,
                evaluation=general_evaluation,
            )

            student_group_evaluations = StudentEvaluation.objects.filter(
                group_evaluation=group_evaluation,
            )

            students = Student.objects.filter(
                group_id=group_id
            )

            students_to_create = students.exclude(
                id__in=student_group_evaluations.values_list(
                    'student_id',
                    flat=True,
                )
            )

            for student_to_create in students_to_create:
                student_evaluations.append(
                    StudentEvaluation(
                        group_evaluation=group_evaluation,
                        student=student_to_create,
                    )
                )

        evaluations.filter(
            group__in=to_delete_group_ids,
        ).delete()

        StudentEvaluation.objects.bulk_create(
            student_evaluations
        )

        return result

    def get_success_url(self):
        return reverse(
            "evaluations:list",
        )


class GroupEvaluationsList(
    GroupEvaluationMixin,
    DataTablesView
):
    ajax_template_name = 'evaluations/group_evaluations.json'

    column_index_map = {
        0: 'evaluation__activity__activity_id',
        1: 'evaluation__activity__learning_target__name',
        2: 'evaluation__activity__learning_target__level',
        3: 'group__name',
        4: 'status',
        5: 'evaluation__due_date',
    }

    template_name = 'evaluations/group_evaluations_list.html'

    def get_items(self):
        return GroupEvaluation.objects.filter(
            group__in=self.request.user.assigned_groups.all(),
            active=True,
        ).select_related(
            'evaluation',
            'group',
            'evaluation__activity',
            'evaluation__activity__learning_target',
        ).prefetch_related(
            'student_evaluations'
        )


class GroupEvaluationPrint(
    GroupEvaluationMixin,
    DetailView,
):
    template_name = 'evaluations/group_evaluation_print.html'
    context_object_name = 'group_evaluation'
    pk_url_kwarg = 'group_evaluation_id'

    def test_func(self, user):
        return user.is_professor

    def get_queryset(self):
        return GroupEvaluation.objects.filter(
            group__in=self.request.user.assigned_groups.all(),
            active=True,
        ).select_related(
            'evaluation',
            'evaluation__activity',
        )


class GroupEvaluate(
    GroupEvaluationMixin,
    UpdateView,
):
    context_object_name = 'group_evaluation'
    form_class = StudentEvaluationFormset
    pk_url_kwarg = 'group_evaluation_id'
    template_name = 'evaluations/evaluate_group.html'

    def get_queryset(self):
        return GroupEvaluation.objects.filter(
            group__in=self.request.user.assigned_groups.all(),
            active=True,
        ).select_related(
            'evaluation'
        ).prefetch_related(
            'student_evaluations'
        )

    def get_group_evaluation(self):
        return get_object_or_404(
            GroupEvaluation,
            id=self.kwargs[self.pk_url_kwarg]
        )

    @property
    def object(self):
        return self.get_group_evaluation()

    def get(self, request, *_, **__):
        group_evaluation = self.get_group_evaluation()

        invite_formset = self.get_formset(
            group_evaluation
        )

        context = {
            'formset': invite_formset,
            'group_evaluation': group_evaluation,
            'section': 'evaluations',
        }

        activity = group_evaluation.evaluation.activity

        initial = {}

        default_identity_and_autonomy_target = activity.identity_and_autonomy_target
        default_coexistence_and_citizenship_target = activity.coexistence_and_citizenship_target
        default_corporality_and_movement_target = activity.corporality_and_movement_target
        default_materials = activity.materials

        if not group_evaluation.override_identity_and_autonomy_target:
            initial['override_identity_and_autonomy_target'] = default_identity_and_autonomy_target

        if not group_evaluation.override_coexistence_and_citizenship_target:
            initial['override_coexistence_and_citizenship_target'] = default_coexistence_and_citizenship_target

        if not group_evaluation.override_corporality_and_movement_target:
            initial['override_corporality_and_movement_target'] = default_corporality_and_movement_target

        if not group_evaluation.override_materials:
            initial['override_materials'] = default_materials

        form = GroupEvaluationForm(
            instance=group_evaluation,
            user=self.request.user,
            initial=initial,
        )

        context['form'] = form

        if self.request.user.has_professor_experience_enabled:
            default_beginning = activity.learning_experience_beginning
            default_development = activity.learning_experience_development
            default_conclusion = activity.learning_experience_conclusion

            if not group_evaluation.override_beginning:
                initial['override_beginning'] = default_beginning

            if not group_evaluation.override_development:
                initial['override_development'] = default_development

            if not group_evaluation.override_conclusion:
                initial['override_conclusion'] = default_conclusion

            context['default_beginning'] = default_beginning
            context['default_development'] = default_development
            context['default_conclusion'] = default_conclusion

        context['default_identity_and_autonomy_target'] = default_identity_and_autonomy_target
        context['default_coexistence_and_citizenship_target'] = default_coexistence_and_citizenship_target
        context['default_corporality_and_movement_target'] = default_corporality_and_movement_target
        context['default_materials'] = default_materials

        return self.render_to_response(context)

    @staticmethod
    def create_changes(group_evaluation, classifications_before):
        classifications_after = StudentEvaluation.objects.filter(
            group_evaluation=group_evaluation
        ).values(
            'id',
            'classification',
        )

        classifications_before_map = {
            classification_before['id']: classification_before['classification']
            for classification_before
            in classifications_before
        }

        classifications_to_create = []

        for classification_after in classifications_after:
            classification_after_id = classification_after['id']
            classification_after_value = classification_after['classification']

            classification_before = classifications_before_map.get(
                classification_after_id,
                None
            )

            if classification_before is not None and classification_before != classification_after_value:
                classifications_to_create.append(
                    StudentEvaluationChange(
                        from_classification=classification_before,
                        to_classification=classification_after_value,
                        student_evaluation_id=classification_after_id,
                    )
                )

        StudentEvaluationChange.objects.bulk_create(
            classifications_to_create
        )

    def post(self, request, *_, **__):
        group_evaluation = self.get_group_evaluation()

        classifications_before = list(
            StudentEvaluation.objects.filter(
                group_evaluation=group_evaluation
            ).values(
                'id',
                'classification'
            )
        )

        formset = self.get_formset(
            group_evaluation,
            request.POST
        )

        activity = group_evaluation.evaluation.activity

        initial = {
            'override_identity_and_autonomy_target': activity.identity_and_autonomy_target,
            'override_coexistence_and_citizenship_target': activity.coexistence_and_citizenship_target,
            'override_corporality_and_movement_target': activity.corporality_and_movement_target,
            'override_materials': activity.materials,
        }

        if request.user.has_professor_experience_enabled:
            initial.update(
                {
                    'override_beginning': activity.learning_experience_beginning,
                    'override_development': activity.learning_experience_development,
                    'override_conclusion': activity.learning_experience_conclusion,
                }
            )

        form = GroupEvaluationForm(
            request.POST,
            instance=group_evaluation,
            user=self.request.user,
            initial=initial,
        )

        if formset.is_valid():
            formset.save()

            if form and form.is_valid():
                form.save()

            self.create_changes(
                group_evaluation,
                classifications_before,
            )
            return redirect('evaluations:group_evaluations_list')

        return self.render_to_response({
            'formset': formset,
            'group_evaluation': group_evaluation,
            'section': 'evaluations',
            'form': form,
        })

    def get_formset(self, instance, data=None):
        return self.form_class(
            instance=instance,
            data=data,
            form_kwargs={
                'user': self.request.user,
            }
        )


class GroupEvaluateFinalize(
    GroupEvaluationMixin,
    RedirectView,
):
    @staticmethod
    def get_queryset():
        return GroupEvaluation.objects.filter(
            active=True,
        )

    def get_redirect_url(self, *args, **kwargs):
        return reverse('evaluations:group_evaluations_list')

    def get(self, request, *args, **kwargs):
        evaluation_id = self.kwargs.get('group_evaluation_id')
        evaluation = get_object_or_404(
            self.get_queryset(),
            pk=evaluation_id,
            status=GroupEvaluation.DRAFT,
        )

        evaluation.status = GroupEvaluation.SENT
        evaluation.save()

        return redirect(
            self.get_redirect_url()
        )


class StudentEvolution(
    GroupEvaluationMixin,
    ListView,
):
    context_object_name = 'student_evaluations'
    template_name = 'evaluations/student_evolution.html'

    def get_queryset(self):
        evaluation = self.get_group_evaluation()
        student = self.get_student()

        student_evaluation = evaluation.student_evaluations.filter(
            student=student
        ).first()

        return student_evaluation.evaluation_changes.all()

    def get_student(self):
        return Student.objects.get(
            pk=self.kwargs['student_id']
        )

    def get_group_evaluation(self):
        return GroupEvaluation.objects.filter(
            group__in=self.request.user.assigned_groups.all(),
            active=True,
        ).get(
            pk=self.kwargs['group_evaluation_id']
        )

    @staticmethod
    def get_evaluation_intervals(group_evaluation, evaluation_changes):
        if not evaluation_changes:
            return [
                (
                    'No evaluado',
                    group_evaluation.created_at.date(),
                    timezone.now().date(),
                )
            ]

        evaluation_changes = list(evaluation_changes)

        result = [
            (
                'No evaluado',
                group_evaluation.created_at.date(),
                evaluation_changes[0].created_at.date()
            ),
        ]

        for i, evaluation_change in enumerate(evaluation_changes):
            if i == 0:
                continue

            result.append(
                (
                    evaluation_changes[i - 1].get_from_classification_display(),
                    evaluation_changes[i - 1].created_at.date(),
                    evaluation_change.created_at.date(),
                )
            )

        result.append(
            (
                evaluation_changes[-1].get_to_classification_display(),
                evaluation_changes[-1].created_at.date(),
                timezone.now().date(),
            )
        )

        return result

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data['student'] = self.get_student()
        context_data['group_evaluation'] = self.get_group_evaluation()

        context_data['evaluation_intervals'] = self.get_evaluation_intervals(
            context_data['group_evaluation'],
            context_data[self.context_object_name],
        )

        return context_data


class AnecdotalRecordList(
    AnecdotalRecordMixin,
    DataTablesView
):
    ajax_template_name = 'anecdotal-records/anecdotal-records.json'

    column_index_map = {
        0: 'last_name',
        1: 'first_name',
        2: 'group__name',
        3: 'list_number',
        4: 'rut',
        5: 'birth_date',
        6: 'created_at',
    }

    template_name = 'anecdotal-records/anecdotal_records_list.html'

    def get_items(self):
        return self.get_students_with_anecdotal_record(
            self.request.user
        )


class AnecdotalRecordDetail(
    AnecdotalRecordMixin,
    DetailView
):
    context_object_name = 'anecdotal_record'
    model = AnecdotalRecord
    pk_url_kwarg = "anecdotal_record_id"
    template_name = 'anecdotal-records/anecdotal_record_detail.html'

    def get_queryset(self):
        return self.get_records(
            self.request.user
        )


class AnecdotalRecordStudentDetail(
    AnecdotalRecordMixin,
    DetailView
):
    context_object_name = 'student'
    model = Student
    pk_url_kwarg = 'student_id'
    template_name = 'anecdotal-records/anecdotal_record_student_detail.html'

    def get_queryset(self):
        return self.get_students_with_anecdotal_record(
            self.request.user
        )


class AnecdotalRecordEdit(
    AnecdotalRecordMixin,
    UpdateView
):
    pk_url_kwarg = "anecdotal_record_id"
    form_class = ProfessorAnecdotalRecordForm
    context_object_name = "anecdotal_record"
    template_name = 'anecdotal-records/anecdotal_records_edit.html'

    def get_success_url(self):
        return reverse(
            'evaluations:anecdotal_records_list'
        )

    def get_form_class(self):
        user = self.request.user

        if user.is_coordinator or user.is_general_coordinator:
            return CoordinatorAnecdotalRecordForm

        return super().get_form_class()

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        user = self.request.user
        form_kwargs['user'] = user

        return form_kwargs

    def get_queryset(self):
        return self.get_records(
            self.request.user
        )

    def form_valid(self, form):
        if not form.instance.created_by:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class AnecdotalRecordCreate(
    AnecdotalRecordMixin,
    CreateView,
):
    form_class = ProfessorAnecdotalRecordForm
    template_name = 'anecdotal-records/anecdotal_records_create.html'

    def get_success_url(self):
        return reverse(
            'evaluations:anecdotal_records_list'
        )

    def test_func(self, user):
        return user.is_professor

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        user = self.request.user
        form_kwargs['user'] = user

        return form_kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EvaluationViewPDF(View):
    def get(self, request):
        group_evaluation_id = request.GET.get('group_evaluation_id')
        group_evaluation = GroupEvaluation.objects.get(id=group_evaluation_id)

        activity_id = request.GET.get('activity_id')
        learning_target_name = request.GET.get('learning_target_name')
        level  = request.GET.get('level')
        group  = request.GET.get('group')
        status = request.GET.get('status')
        due_date = request.GET.get('due_date')
        template = get_template('evaluations/report_in_pdf_evaluation.html')

        data = {
            'achieved': group_evaluation.achieved_count(), 
            'moderately_accomplished': group_evaluation.moderately_accomplished_count(), 
            'not_achieved': group_evaluation.not_achieved_count(), 
            'not_evaluated': group_evaluation.not_evaluated_count()
        }

        charts = generate_pie_and_bar_charts(data, activity_id)

        context = {
            'title': 'Reporte_{}.pdf'.format(activity_id),
            'activity_id': activity_id, 
            'learning_target_name': learning_target_name, 
            'level': level, 
            'group': group, 
            'status': status, 
            'due_date': due_date,
            'group_evaluation': group_evaluation,
            'charts': charts,
            'protocol': request.scheme,
            'domain': request.headers['Host'],
        }

        html = template.render(context)

        response = HttpResponse(content_type = 'application/pdf')
        response['Content-Disposition'] = 'filename="Reporte_{}.pdf"'.format(activity_id)
        
        pisaStatus = pisa.CreatePDF(
            BytesIO(html.encode('UTF-8')), 
            dest=response, 
            link_callback=None
        )

        if(pisaStatus.err):
            return HttpResponse('We had some erros <pre>' + html + '</pre>')
        else:
            return response

class AnecdotalRecordStudentDetailPDF(View):
    def get(self, request, student_id):
        anecdotal_record_id = request.GET.get('anecdotal_record_id')
        anecdotal_record = AnecdotalRecord.objects.get(id = anecdotal_record_id)
        student = anecdotal_record.student
        
        template = get_template('anecdotal-records/report_in_pdf_anecdotal_records.html')
        
        context = {
            'title': 'Registro_anecdotico_{}.pdf'.format(anecdotal_record_id),
            'anecdotal_record': anecdotal_record,
            'student': student,
            'protocol': request.scheme,
            'domain': request.headers['Host'],
        }

        html = template.render(context)

        response = HttpResponse(content_type = 'application/pdf')
        response['Content-Disposition'] = 'filename="Registro_anecdotico_{}.pdf"'.format(anecdotal_record_id)
        
        pisaStatus = pisa.CreatePDF(
            BytesIO(html.encode('UTF-8')), 
            dest=response, 
            link_callback=None
        )

        if(pisaStatus.err):
            return HttpResponse('We had some erros <pre>' + html + '</pre>')
        else:
            return response