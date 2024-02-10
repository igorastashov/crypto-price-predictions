import matplotlib.pyplot as plt
import io
from aiogram.types import BufferedInputFile


async def plot_history(stock_history, tickers):
    """
    Визуализация исторических данных.

    :param stock_history: Данные из функции `pre_processing/data_loader`;
    :param tickers: Акция
    :return: Изображение BufferedInputFile сохраненное в буфере
    """
    # Create the graph
    plt.figure(figsize=(12, 5))
    plt.plot(stock_history[tickers])
    plt.title(f'{tickers[0]} Исторические данные стоимости')
    plt.xlabel('Дата')
    plt.ylabel('Стоимость')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    file = BufferedInputFile(buf.read(), filename="stock_price_history.png")
    return file


async def plot_predict(data):
    """
    Простая визуализация предсказания
    :param data: Подготовленные данные для визуализации см. `post_processing.py: get_data_for_plot`
    :return: Изображение BufferedInputFile сохраненное в буфере
    """
    plt.figure()
    plt.plot(data[['history', 'prediction']])
    plt.fill_between(x=data.index, y1=data['left_int'], y2=data['right_int'], color='b', alpha=.1)
    plt.legend(['history', 'prediction'])
    plt.xticks(rotation=90)
    plt.tick_params(axis="x", labelsize=6)
    plt.title(f"Прогноз")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot = BufferedInputFile(buf.read(), filename="predict_price.png")
    return plot
