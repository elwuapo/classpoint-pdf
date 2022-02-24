from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from ..base.models import BaseModel
from ..groups.models import Group
from ..learning_targets.models import Activity
from ..schools.models import School
from ..students.models import Student
from ..users.models import User


class GeneralEvaluation(BaseModel):
    activity = models.ForeignKey(
        Activity,
        verbose_name='Actividad',
        on_delete=models.CASCADE,
    )

    due_date = models.DateField(
        verbose_name='Fecha de entrega',
    )

    school = models.ForeignKey(
        School,
        verbose_name='Escuela',
        on_delete=models.CASCADE,
    )

    def groups(self):
        return GroupEvaluation.objects.filter(
            evaluation=self
        ).select_related(
            'group'
        ).only(
            'group'
        ).values_list(
            'group',
            flat=True
        )

    @cached_property
    def status(self):
        if self.completion_percent == 100:
            return 'Completada'

        if timezone.now().date() < self.due_date:
            return 'Vigente'

        return 'Atrasada'

    def status_class(self):
        if self.status == 'Completada':
            return 'success'
        elif self.status == 'Atrasada':
            return 'danger'
        return 'warning'

    @cached_property
    def completion_percent(self):
        group_evaluations = self.group_evaluations
        total_items = group_evaluations.count()

        if total_items == 0:
            return 100

        completed_items = group_evaluations.filter(
            status=GroupEvaluation.SENT
        ).count()

        return round(
            completed_items / total_items,
            2
        ) * 100

    class Meta:
        verbose_name = 'Evaluación general'
        verbose_name_plural = 'Evaluaciones generales'


class GroupEvaluation(BaseModel):
    DRAFT = 0
    SENT = 1

    STATUS_CHOICES = [
        (DRAFT, 'Borrador'),
        (SENT, 'Enviada'),
    ]

    evaluation = models.ForeignKey(
        GeneralEvaluation,
        verbose_name='Evaluación',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='group_evaluations'
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name='Grupo',
        related_name='evaluations'
    )

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name='Estado',
    )

    override_beginning = models.TextField(
        'Inicio',
        blank=True,
        null=True,
        db_index=True,
    )

    override_development = models.TextField(
        'Desarrollo',
        blank=True,
        null=True,
        db_index=True,
    )

    override_conclusion = models.TextField(
        'Conclusiones',
        blank=True,
        null=True,
        db_index=True,
    )

    override_identity_and_autonomy_target = models.TextField(
        'Identidad y autonomía',
        blank=True,
        null=True,
    )
    override_coexistence_and_citizenship_target = models.TextField(
        'Convivencia y ciudadanía',
        blank=True,
        null=True,
    )
    override_corporality_and_movement_target = models.TextField(
        'Corporalidad y movimiento',
        blank=True,
        null=True,
    )

    override_materials = models.TextField(
        'Materiales',
        blank=True,
        null=True,
    )

    def sent(self):
        return self.status == GroupEvaluation.SENT

    def draft(self):
        return self.status == GroupEvaluation.DRAFT

    def student_evaluations_ordered(self):
        return self.student_evaluations.select_related(
            'student',
        ).order_by(
            'student__list_number',
        )

    def evaluation_count(self):
        return self.student_evaluations.count()

    def get_evaluation_count(self, evaluation_type):
        return self.student_evaluations.order_by(
            'student_id',
            '-id'
        ).distinct(
            'student_id',
        ).filter(
            classification=evaluation_type
        ).count()

    def achieved_count(self):
        return self.get_evaluation_count(
            StudentEvaluation.ACHIEVED
        )

    def moderately_accomplished_count(self):
        return self.get_evaluation_count(
            StudentEvaluation.MODERATELY_ACCOMPLISHED,
        )

    def not_achieved_count(self):
        return self.get_evaluation_count(
            StudentEvaluation.NOT_ACHIEVED,
        )

    def not_evaluated_count(self):
        return self.get_evaluation_count(
            StudentEvaluation.NOT_EVALUATED,
        )

    @property
    def needs_remedial(self):
        if self.status == self.DRAFT:
            return False

        remedial_students = (
            self.not_achieved_count() +
            self.not_evaluated_count()
        )

        total_students = self.evaluation_count()

        remedial_students_percent = (
            remedial_students / total_students
        ) * 100

        return remedial_students_percent > 20

    class Meta:
        verbose_name = 'Evaluación del grupo'
        verbose_name_plural = 'Evaluaciones del grupo'


class StudentEvaluation(BaseModel):
    NOT_EVALUATED = 1
    NOT_ACHIEVED = 3
    MODERATELY_ACCOMPLISHED = 5
    ACHIEVED = 7

    CLASSIFICATION_CHOICES = [
        (ACHIEVED, 'Nivel 3'),
        (MODERATELY_ACCOMPLISHED, 'Nivel 2'),
        (NOT_ACHIEVED, 'Nivel 1'),
        (NOT_EVALUATED, 'Alumno ausente')
    ]

    group_evaluation = models.ForeignKey(
        GroupEvaluation,
        on_delete=models.CASCADE,
        verbose_name='Evaluación del grupo',
        related_name='student_evaluations'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        verbose_name='Estudiante',
    )

    classification = models.PositiveSmallIntegerField(
        choices=CLASSIFICATION_CHOICES,
        default=NOT_EVALUATED,
        verbose_name='Clasificación',
    )

    annotations = models.TextField(
        blank=True,
        default='',
        verbose_name='Anotaciones',
    )

    @property
    def finished(self):
        return self.classification == self.ACHIEVED

    class Meta:
        ordering = [
            'student__first_name',
            'student__last_name',
        ]
        verbose_name = 'Evaluación del estudiante'
        verbose_name_plural = 'Evaluaciones del estudiante'


class StudentEvaluationChange(BaseModel):
    student_evaluation = models.ForeignKey(
        StudentEvaluation,
        on_delete=models.CASCADE,
        verbose_name='Evaluación del grupo',
        related_name='evaluation_changes'
    )

    from_classification = models.PositiveSmallIntegerField(
        choices=StudentEvaluation.CLASSIFICATION_CHOICES,
        verbose_name='Clasificación anterior',
    )

    to_classification = models.PositiveSmallIntegerField(
        choices=StudentEvaluation.CLASSIFICATION_CHOICES,
        verbose_name='Clasificación actual',
    )

    class Meta:
        verbose_name = 'Evolución del estudiante'
        verbose_name_plural = 'Evolución de los estudiantes'


class AnecdotalRecord(BaseModel):
    student = models.ForeignKey(
        Student,
        verbose_name='Estudiante',
        on_delete=models.CASCADE,
        related_name='anecdotal_records',
    )

    activity = models.ForeignKey(
        Activity,
        verbose_name='Actividad',
        on_delete=models.CASCADE,
        related_name='student_anecdotal_records',
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        User,
        verbose_name='Creado por',
        help_text='Usuario que creó este registro',
        related_name='created_records',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    observation_time = models.PositiveSmallIntegerField(
        verbose_name='Tiempo de observación',
        help_text='Tiempo en minutos que tomó la observación',
        default=5,
    )

    observation_source = models.CharField(
        max_length=255,
        verbose_name='Fuente de observación',
    )

    observed_behaviour = models.TextField(
        verbose_name='Conducta observada',
        blank=True,
        default='',
    )

    interpretation = models.TextField(
        verbose_name='Interpretación',
        blank=True,
        default='',
    )

    comments = models.TextField(
        verbose_name='Comentarios',
        help_text='Comentarios del coordinador',
        blank=True,
        default='',
    )

    image = models.ImageField(
        verbose_name='Imagen',
        help_text='Adjunte una imagen',
        blank=True,
        null=True,
        upload_to='academic-records/images/'
    )

    def __str__(self):
        return f'{self.student}'

    class Meta:
        verbose_name = 'Registro anecdótico'
        verbose_name_plural = 'Registros anecdóticos'
