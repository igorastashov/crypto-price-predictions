import pandas as pd
import yfinance as yf


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


async def data_all(start_date, end_date, tickers):
    """
    Функция выгрузки данных в нужном формате с yfinance
    """
    df = pd.DataFrame(yf.download(tickers[0], start=start_date, end=end_date))
    return df


async def data_grp(data, tickers):
    """
    Функция группировки данных по дате и средней стоимости
    """
    data = data.reset_index()
    df_grp = data.groupby(data['Date'].dt.strftime("%B %Y"))[tickers[0]].mean().reset_index()
    df_grp['Date'] = pd.to_datetime(df_grp['Date'], format='%B %Y')  # Преобразование столбца Date в формат даты
    df_grp = df_grp.sort_values(by='Date')  # Сортировка по столбцу Date
    return df_grp

