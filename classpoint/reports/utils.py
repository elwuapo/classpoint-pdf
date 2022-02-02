from turtle import clear
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def get_dot_name(value):
    return str(value).replace(',', '.')

def generate_bar_and_line_char(bar_graph_data, line_graph_data):
    studens = [ name for name, avg in bar_graph_data ]
    calification = [ avg for name, avg in bar_graph_data ]
    color = ['#4688f1', '#d9453d'] 

    dates = [ data[0] +'(' + str(index) +')' for index, data in enumerate(line_graph_data)]
    grade = [ float(group_evaluation) for date, evaluation, group_evaluation in line_graph_data]
    student = [ evaluation for date, evaluation, group_evaluation in line_graph_data]

    fig, axs = plt.subplots(1, 2, figsize=(15, 5), sharey=True)

    axs[0].bar(studens, calification, color=color, width=0.4)
    axs[0].set_xlabel('Actividad')
    axs[0].set_ylabel('Desempeño')
    axs[0].set_title('Gráfico Comparativo')

    if(line_graph_data):
        for index, valor in enumerate(calification):
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
    labels_pie = [ name for name, avg in data if avg != 0 ]
    valors_pie = [ avg for name, avg in data if avg != 0 ]
    explode = tuple([ 0.05 for name, avg in data if avg != 0 ])
    colors_pie = list()

    labels_bar = [ name for name, avg in data ]
    valors_bar = [ avg for name, avg in data ]
    colors_bar = ['#689f38', '#4688f1', '#d9453d']

    for label in labels_pie:
        if label == 'Logrado':
            colors_pie.append('#689f38')
        elif label == 'Medianamente logrado':
            colors_pie.append('#4688f1')
        else:
            colors_pie.append('#d9453d')

    if(valors_pie):
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))
        
        axs[1].pie(
            valors_pie,
            explode = explode,
            labels  = labels_pie,
            colors  = colors_pie,
            autopct = '%1.1f%%',
            startangle=90
        )

        axs[1].set_title('Evaluaciones')

        axs[0].bar(
            labels_bar,
            valors_bar,
            width=0.4,
            color=colors_bar,
        )

        axs[0].set_xlabel('Escala de Apreciación')
        axs[0].set_ylabel('Cantidad de evaluaciones')
        axs[0].set_title(core)

        for index, valor in enumerate(valors_bar):
            axs[0].text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/report_by_core_chart.JPEG'

        plt.savefig('classpoint/' + image_path)
    else:
        fig, ax = plt.subplots(figsize=(15, 5))

        ax.bar(
            labels_bar,
            valors_bar,
            width=0.4,
            color=colors_bar,
        )

        ax.set_xlabel('Escala de Apreciación')
        ax.set_ylabel('Cantidad de evaluaciones')
        ax.set_title(core)

        for index, valor in enumerate(valors_bar):
            ax.text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/report_by_core_chart.JPEG'

        plt.savefig('classpoint/' + image_path)

    return image_path

def generate_pie_and_bar_charts(data):
    labels = ['Logrado', 'Medianamente Logrado', 'Por Logrado']
    colors = ['#689f38', '#4688f1', '#d9453d']
    valors = [data.get('achieved'), data.get('moderately_accomplished'), data.get('not_achieved')]
    explode = tuple([ 0.05 for e in valors])

    if(data.get('achieved') != 0 or data.get('moderately_accomplished') != 0 or data.get('not_achieved') != 0):
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))
    
        axs[1].pie(
            valors,
            explode = explode,
            labels  = labels,
            colors  = colors,
            autopct = '%1.1f%%',
            startangle=90
        )

        axs[1].set_title('Evaluaciones')

        axs[0].bar(
            labels,
            valors,
            width=0.4,
            color=colors,
        )

        axs[0].set_xlabel('Escala de Apreciación')
        axs[0].set_ylabel('Cantidad de alumnos')
        axs[0].set_title(data.get('core_name'))

        for index, valor in enumerate(valors):
            axs[0].text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/{}_chart.JPEG'.format(data.get('abbreviation'))

        plt.savefig('classpoint/' + image_path)
    else:
        fig, ax = plt.subplots(figsize=(15, 5))

        ax.bar(
            labels,
            valors,
            width=0.4,
            color=colors,
        )

        ax.set_xlabel('Escala de Apreciación')
        ax.set_ylabel('Cantidad de alumnos')
        ax.set_title(data.get('core_name'))

        for index, valor in enumerate(valors):
            ax.text(index - 0.05, (valor/2) + 0.025, valor)

        image_path = 'media/pdf-charts/{}_chart.JPEG'.format(data.get('abbreviation'))

        plt.savefig('classpoint/' + image_path)

    return image_path