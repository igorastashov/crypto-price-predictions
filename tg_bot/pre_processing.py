import yfinance as yf
import pandas as pd


async def data_loader(start_date, end_date, tickers, col_value):
    """
    Загрузка данных с yfinance.

    :param start_date: Время начала рассмотрения данных;
    :param end_date: Время окончания рассмотрения данных;
    :param tickers: Акции для загрузки;
    :param col_value: Колонка для парсинга с yfinance;
    :return: Таблица загруженных данных со столбцом 'col_value'.
    """

    data = pd.DataFrame(columns=tickers)
    for ticker in tickers:
        data[ticker] = yf.download(ticker, start_date, end_date)[col_value]
    return data
