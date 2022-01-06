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
    axs[0].set_title('Grafico Comparativo')

    if(line_graph_data):
        for value in enumerate(calification):
            axs[0].text(value[0] - 0.05, value[1] + 0.05, value[1])

    axs[1].plot(dates, student, color='#4688f1')
    axs[1].plot(dates, grade, color='#d9453d')
    axs[1].set_xlabel('Fecha de evaluación')
    axs[1].set_ylabel('Escala de apreciación')
    axs[1].set_title('Evolución del aprendizaje')

    plt.savefig('classpoint/static/charts/chart.JPEG')

    return 'charts/chart.JPEG'


def generate_bar_chart(data):
    rating_scale = [ name for name, avg in data ]
    number_of_evaluations = [ avg for name, avg in data ]
    colors = ['#689f38', '#4688f1', '#d9453d']

    fig1, ax1 = plt.subplots()

    ax1.bar(rating_scale, 
        number_of_evaluations, 
        color=colors, 
        width=0.4
    )

    ax1.set_xlabel('Escala de Apreciación')
    ax1.set_ylabel('Cantidad de evaluaciones')

    plt.savefig('classpoint/static/charts/bar_chart.JPEG')

    return 'charts/bar_chart.JPEG'

def generate_pie_chart(data):
    rating_scale = [ name for name, avg in data if avg != 0 ]
    number_of_evaluations = [ avg for name, avg in data if avg != 0 ]
    explode = tuple([ 0.05 for name, avg in data if avg != 0 ])
    colors = list()

    for element in rating_scale:
        if element == 'Logrado':
            colors.append('#689f38')
        elif element == 'Medianamente logrado':
            colors.append('#4688f1')
        else:
            colors.append('#d9453d')

    fig1, ax1 = plt.subplots()

    ax1.pie(number_of_evaluations, 
        explode=explode, 
        colors = colors, 
        labels=rating_scale, 
        autopct='%1.1f%%', 
        startangle=90
    )

    ax1.axis('equal')  
    plt.tight_layout()
    
    plt.savefig('classpoint/static/charts/pie_chart.JPEG')

    return 'charts/pie_chart.JPEG'