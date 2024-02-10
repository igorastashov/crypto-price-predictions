import pmdarima as pm


async def arima_model(data, ticker, periods):
    """
    AUTO ARIMA.

    :param data: Спарсенный датафрэйм;
    :param ticker: Акция для которой предсказываем;
    :param periods: Горизонт предсказания;
    :return: Предсказание и доверительный интервал.
    """
    model = pm.auto_arima(y=data[ticker],
                          start_p=0, start_q=0, d=0,
                          stepwise=True,
                          suppress_warnings=True,
                          error_action="ignore",
                          max_p=7, max_q=7,
                          race=False)
    predict, conf = model.predict(n_periods=periods, return_conf_int=True)
    return predict, conf
