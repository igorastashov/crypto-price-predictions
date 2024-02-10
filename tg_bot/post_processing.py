import pandas as pd
from datetime import timedelta


async def post_processing_data(model_predict, end_date, periods, conf):
    """
    Список дней с предсказанным значением и отклонением в лево и право.

    :param model_predict: Предсказание модели;
    :param end_date: Последняя временная отметка после которой строится предсказание;
    :param periods: Горизонт предказания;
    :param conf: Доверительный интервал предсказания;
    :return: Таблица с предсказанием.
    """
    add_dates = [(end_date + timedelta(day)).strftime('%Y-%m-%d') for day in range(periods)]
    predict_df = pd.DataFrame(model_predict.values, columns=['prediction'], index=add_dates)
    predict_df['left_int'] = conf.T[0]
    predict_df['right_int'] = conf.T[1]
    return predict_df


async def get_data_for_plot(data, back_days, ticker_predict, predict_df):
    """
    Таблица`BACK_DAYS` с пустыми столбцами:`prediction`, `left_int`, `right_in`.
    А так же подставленный снизу `predict_df` с предсказаниями на `PERIODS`.

    :param data: загруженные данные с yfinance см. `pre_processing.py: data_loader`;
    :param back_days: Последнее кол-во дней для отображения на итоговом графике совместно с предсказанием;
    :param ticker_predict: Акция для предсказания;
    :param predict_df: Таблица с предсказаниями.
    :return: Составленная таблица с предыдущими значениями и предсказанными + доверительный инетрвал.
    """
    prev_data = data[-back_days:]
    prev_data = prev_data.assign(prediction=pd.NA, left_int=pd.NA, right_int=pd.NA)
    prev_data = prev_data.rename(columns={ticker_predict: 'history'})
    prev_data = prev_data[['prediction', 'left_int', 'right_int', 'history']]
    prev_data.index = prev_data.index.strftime('%Y-%m-%d')
    concat_data = pd.concat([prev_data, predict_df])

    return concat_data
