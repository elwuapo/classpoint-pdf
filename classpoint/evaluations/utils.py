import functools
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')


def memoize(func):
    cache = func.cache = {}

    @functools.wraps(func)
    def memoized_func(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return memoized_func


def generate_pie_and_bar_charts(data, activity_id):
    labels = ['Logrado', 'Medianamente Logrado', 'Por Logrado', 'Ausentes']
    colors = ['#689f38', '#4688f1', '#d9453d', '#FCE205']

    data_values = [
        data.get('achieved'),
        data.get('moderately_accomplished'),
        data.get('not_achieved'),
        data.get('not_evaluated'),
    ]

    explode = tuple([0.05] * len(data_values))

    if(
        data.get('achieved') != 0 or
        data.get('moderately_accomplished') != 0 or
        data.get('not_achieved') != 0 or
        data.get('not_evaluated') != 0
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

        axs[0].bar(
            labels,
            data_values,
            width=0.4,
            color=colors,
        )

        axs[0].set_xlabel('Escala de Apreciación')
        axs[0].set_ylabel('Cantidad de alumnos')

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

        for index, valor in enumerate(data_values):
            ax.text(index - 0.05, (valor/2) + 0.025, valor)

    image_path = f'media/pdf-charts/{activity_id}_chart.JPEG'

    plt.savefig('classpoint/' + image_path)

    return image_path
