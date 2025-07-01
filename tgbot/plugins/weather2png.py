import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import io
from matplotlib.animation import FuncAnimation

def create_weather_gif(day_temp, night_temp, precipitation, filename='weather_animation.gif'):
    """
    Функция создает анимированный график температуры и осадков за неделю.
    :param day_temp: список чисел дневных температур
    :param night_temp: список чисел ночных температур
    :param precipitation: список чисел количества осадков
    :param filename: название файла для сохранения GIF-анимаций
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame):
        # Обновляем график на каждом кадре
        plt.cla()  # очистка предыдущего графика
        
        # График дневной температуры красным цветом
        ax.plot(range(len(day_temp[:frame+1])), day_temp[:frame+1], color="red", label="Дневная температура")
        
        # График ночной температуры черным цветом
        ax.plot(range(len(night_temp[:frame+1])), night_temp[:frame+1], color="black", label="Ночная температура")
        
        # Столбцы осадков голубым цветом
        ax.bar(range(len(precipitation[:frame+1])), precipitation[:frame+1], alpha=0.7, color="blue", label="Осадки")
        
        # Оформление графика
        ax.set_xlabel("День недели")
        ax.set_ylabel("Температура / Количество осадков")
        ax.legend(loc="upper left")
        ax.grid(True)
        plt.title(f"Погодные условия (день {frame + 1})")

    # Создание анимации с полным диапазоном дней
    animation = FuncAnimation(fig, update, frames=range(len(day_temp)), interval=500, repeat=False)
    
    # Экспорт анимации в GIF-файл с использованием встроенного писателя
    animation.save(filename, writer='pillow', fps=1)

    plt.close()

def create_static_weather_chart(day_temp, night_temp, precipitation, days, filename='weather_chart.png'):
    """
    Функция строит статический график погоды за неделю и сохраняет его в виде PNG.
    :param day_temp: список чисел дневных температур
    :param night_temp: список чисел ночных температур
    :param precipitation: список чисел количества осадков
    :param days: список строк с названиями дней недели
    :param filename: название файла для сохранения PNG
    """
    plt.switch_backend('Agg')
    # Настройки графики
    plt.figure(figsize=(8, 6))

    # Линии дневной и ночной температуры с увеличенной толщиной линии
    plt.plot(days, day_temp, color="red", linewidth=4, marker='o', markersize=8, label="Дневная температура")
    plt.plot(days, night_temp, color="black", linewidth=4, marker='s', markersize=8, label="Ночная температура")

    # Столбчатые осадки
    plt.bar(np.arange(len(precipitation)), precipitation, width=0.4, align='center', alpha=0.7, color="blue", label="Осадки")

    # Оформление оси X и Y
    plt.xlabel("День недели")
    plt.ylabel("Температура / Количество осадков")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.title("График погоды за неделю")

    # Сохранение изображения
    plt.savefig(filename, bbox_inches='tight', dpi=100)
    plt.close()

def create_smooth_weather_chart(day_temp, night_temp, precipitation, days, spo='',footer="Дни недели",ymin=-30,ymax=30): # filename='smooth_weather_chart.png'):
    """
    Функция строит гладкий график погоды за неделю с заданным диапазоном температур.
    :param day_temp: список чисел дневных температур
    :param night_temp: список чисел ночных температур
    :param precipitation: список чисел количества осадков
    :param days: список строк с названиями дней недели
    :param filename: название файла для сохранения PNG
    """
    # Гладкая аппроксимация сплайном
    x_new = np.linspace(0, len(days)-1, 300)  # Генерируем много новых точек между существующими днями
    spl_day = make_interp_spline(range(len(day_temp)), day_temp, k=3)  # Сплайн-аппроксимация дневных температур
    smooth_day_temp = spl_day(x_new)

    # Настройки графики
    plt.switch_backend('Agg')
    plt.figure(figsize=(8, 4))

    # Плавные линии дневной и ночной температуры с увеличенной толщиной линии
    plt.plot(x_new, smooth_day_temp, color="red", linewidth=4, label="Дневная температура")

    if night_temp:
        spl_night = make_interp_spline(range(len(night_temp)), night_temp, k=3)  # Сплайн-аппроксимация ночных температур
        smooth_night_temp = spl_night(x_new)
        plt.plot(x_new, smooth_night_temp, color="black", linewidth=4, label="Ночная температура")

    # Столбчатые осадки остаются прямыми, т.к. не имеют смысла превращать их в кривые
    plt.bar(np.arange(len(precipitation)), precipitation, width=0.4, align='center', alpha=0.7, color="blue", label="Осадки (мм)")

    # Оформление оси X и Y
    plt.xlabel(footer)
    plt.ylabel("Температура / Количество осадков (mm)")
    plt.ylim(ymin, ymax)  # Устанавливаем диапазон температур -30, 40)
    plt.xticks(range(len(days)), days, rotation=45)
    plt.legend()
    plt.grid(True)
    plt.title(f"Прогноз погоды {spo}")

    # # Сохранение изображения
    # plt.savefig(filename, bbox_inches='tight', dpi=100)
    # plt.close()

    # Сохраняем график в памяти
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    buffer.seek(0)  # Перемещаемся обратно в начало буфера
    return buffer
