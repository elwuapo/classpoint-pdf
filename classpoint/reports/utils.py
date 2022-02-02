import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')


def get_dot_name(value):
    return str(value).replace(',', '.')


def generate_bar_and_line_char(bar_graph_data, line_graph_data):
    student_names = [name for name, avg in bar_graph_data]
    classifications = [avg for name, avg in bar_graph_data]
    color = ['#4688f1', '#d9453d']

    dates = [
        f'{data[0]}({index})'
        for index, data
        in enumerate(line_graph_data)
    ]

    grade = [
        float(group_evaluation)
        for date, evaluation, group_evaluation
        in line_graph_data
    ]

    student = [
        evaluation
        for date, evaluation, group_evaluation
        in line_graph_data
    ]

    fig, axs = plt.subplots(1, 2, figsize=(15, 5), sharey=True)

    axs[0].bar(
        student_names,
        classifications,
        color=color,
        width=0.4
    )

    axs[0].set_xlabel('Actividad')
    axs[0].set_ylabel('Desempeño')
    axs[0].set_title('Gráfico Comparativo')

    if line_graph_data:
        for index, valor in enumerate(classifications):
            axs[0].text(index - 0.05, (valor/2) + 0.025, valor)

    axs[1].plot(dates, student, color='#4688f1')
    axs[1].plot(dates, grade, color='#d9453d')
    axs[1].set_xlabel('Fecha de evaluación')
    axs[1].set_ylabel('Escala de apreciación')
    axs[1].set_title('Evolución del aprendizaje')

    image_path = 'media/pdf-charts/report_by_objective_chart.JPEG'
    plt.savefig('classpoint/' + image_path)

    return image_path


def generate_bar_and_pie_chart(data, core):
    pie_labels = [name for name, avg in data if avg != 0]
    pie_values = [avg for name, avg in data if avg != 0]
    explode = tuple([0.05 for name, avg in data if avg != 0])
    pie_colors = list()

    bar_labels = [name for name, avg in data]
    bar_values = [avg for name, avg in data]
    bar_colors = ['#689f38', '#4688f1', '#d9453d']

    for label in pie_labels:
        if label == 'Logrado':
            pie_colors.append('#689f38')
        elif label == 'Medianamente logrado':
            pie_colors.append('#4688f1')
        else:
            pie_colors.append('#d9453d')

    if pie_values:
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))

        axs[1].pie(
            pie_values,
            explode=explode,
            labels=pie_labels,
            colors=pie_colors,
            autopct='%1.1f%%',
            startangle=90
        )

        axs[1].set_title('Evaluaciones')

        axs[0].bar(
            bar_labels,
            bar_values,
            width=0.4,
            color=bar_colors,
        )

        axs[0].set_xlabel('Escala de Apreciación')
        axs[0].set_ylabel('Cantidad de evaluaciones')
        axs[0].set_title(core)

        for index, valor in enumerate(bar_values):
            axs[0].text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/report_by_core_chart.JPEG'

        plt.savefig('classpoint/' + image_path)
    else:
        fig, ax = plt.subplots(figsize=(15, 5))

        ax.bar(
            bar_labels,
            bar_values,
            width=0.4,
            color=bar_colors,
        )

        ax.set_xlabel('Escala de Apreciación')
        ax.set_ylabel('Cantidad de evaluaciones')
        ax.set_title(core)

        for index, valor in enumerate(bar_values):
            ax.text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/report_by_core_chart.JPEG'

        plt.savefig('classpoint/' + image_path)

    return image_path


def generate_pie_and_bar_charts(data):
    labels = ['Logrado', 'Medianamente Logrado', 'Por Logrado']
    colors = ['#689f38', '#4688f1', '#d9453d']

    data_values = [
        data.get('achieved'),
        data.get('moderately_accomplished'),
        data.get('not_achieved')
    ]

    explode = tuple([0.05] * len(data_values))

    if(
        data.get('achieved') != 0 or
        data.get('moderately_accomplished') != 0 or
        data.get('not_achieved') != 0
    ):
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))

        axs[1].pie(
            data_values,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90
        )

        axs[1].set_title('Evaluaciones')

        axs[0].bar(
            labels,
            data_values,
            width=0.4,
            color=colors,
        )

        axs[0].set_xlabel('Escala de Apreciación')
        axs[0].set_ylabel('Cantidad de alumnos')
        axs[0].set_title(data.get('core_name'))

        for index, valor in enumerate(data_values):
            axs[0].text(index - 0.05, (valor/2) + 0.025, valor)

    else:
        fig, ax = plt.subplots(figsize=(15, 5))

        ax.bar(
            labels,
            data_values,
            width=0.4,
            color=colors,
        )

        ax.set_xlabel('Escala de Apreciación')
        ax.set_ylabel('Cantidad de alumnos')
        ax.set_title(data.get('core_name'))

        for index, valor in enumerate(data_values):
            ax.text(index - 0.05, (valor/2) + 0.025, valor)

    abbreviation = data.get('abbreviation')
    image_path = f'media/pdf-charts/{abbreviation}_chart.JPEG'

    plt.savefig('classpoint/' + image_path)

    return image_path
