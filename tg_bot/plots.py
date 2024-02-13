import io
import plotly.graph_objects as go
import matplotlib.pyplot as plt
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
    plt.title(f"{tickers[0]} Исторические данные стоимости")
    plt.xlabel("Дата")
    plt.ylabel("Стоимость")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    file = BufferedInputFile(buf.read(), filename="stock_price_history.png")
    return file


async def plot_predict(data):
    """
    Простая визуализация предсказания
    :param data: Подготовленные данные для визуализации см.
     `post_processing.py: get_data_for_plot`
    :return: Изображение BufferedInputFile сохраненное в буфере
    """
    plt.figure()
    plt.plot(data[["history", "prediction"]])
    plt.fill_between(
        x=data.index, y1=data["left_int"], y2=data["right_int"], color="b", alpha=0.1
    )
    plt.legend(["history", "prediction"])
    plt.xlabel("Дата")
    plt.xticks(rotation=90)
    plt.ylabel("Стоимость")
    plt.tick_params(axis="x", labelsize=6)
    plt.title("Прогноз")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plot = BufferedInputFile(buf.read(), filename="predict_price.png")
    return plot


#Визуализация с помощью библиотеки plotly среднемесячной цены криптовалют

async def viz_avg(df_grp, tickers):
    
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_grp['Date'], y=df_grp[tickers[0]], mode='lines+markers', name=tickers[0]))

    fig.update_layout(
        title='Динамика среднемесячной стоимости по периоду ' + tickers[0],
        xaxis_title='Месяц - год',
        yaxis_title='Стоимость , USD',
        xaxis_tickangle=-45,
    )

    img_bytes = fig.to_image(format="png")

    file = BufferedInputFile(img_bytes, filename="avg_price.png")
    
    return file


#Визуализация данных стоимости криптовалют в виде свечей с помощью библиоткеи plotly

async def viz_candle(all_data):

    fig = go.Figure(data=[go.Candlestick(x=all_data.index, open=all_data['Open'], high=all_data['High'], low=all_data['Low'], close=all_data['Close'])])
    fig.show()


    img_bytes = fig.to_image(format="png")
    file = BufferedInputFile(img_bytes, filename="candle_price.png")
    return file
    