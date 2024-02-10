import asyncio
import logging
from typing import List

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from aiogram.types import BufferedInputFile
from aiogram.filters.state import State, StatesGroup
import io
from aiogram import F

from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, F, Router, html

import pmdarima as pm

from pre_processing import data_loader
from plots import plot_history, plot_predict



# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "6879124162:AAEOc-Fs1zejw552nMZM-DiYorjJk6OFr5U"
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


# async def generate_stock_graph(start_date, end_date):
#     tickers = ['BTC-USD']
#     # start_date = '2023-01-01'
#     # end_date = datetime.now()
#
#     stock_history = pd.concat((yf.download(ticker,
#                                            start=start_date,
#                                            end=end_date).assign(tkr=ticker) for ticker in tickers), ignore_index=False)
#
#     # Create the graph
#     plt.figure(figsize=(12, 5))
#     plt.plot(stock_history['Adj Close'])
#     plt.title(f'{tickers[0]} Stock Price History')
#     plt.xlabel('Date')
#     plt.ylabel('Price')
#
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png')
#     buf.seek(0)
#     file = BufferedInputFile(buf.read(), filename="stock_price_history.png")
#     return file


# async def data_loader():
#     start_date = '2023-01-01'
#     end_date = datetime.now()
#     tickers = ['BTC-USD']
#
#     df = yf.download(tickers[0], start=start_date, end=end_date)
#     data = df[['Adj Close']].copy()
#     data.columns = data.columns.str.lower()
#     return data, df


async def predict(data, df):
    model = pm.auto_arima(y=data['adj close'],
                        start_p=1,
                        start_q=1,
                        d=1,
                        stepwise=True,
                        suppress_warnings=True,
                        error_action="ignore",
                        max_p=7,
                        max_q=7,
                        race=False)
    pred, conf = model.predict(n_periods=7, return_conf_int=True)
    today = datetime.now()
    add_dates = [(today + timedelta(day)).strftime('%Y-%m-%d') for day in range(7)]
    pred_df = pd.DataFrame(pred.values, columns=['prediction'], index=add_dates)
    pred_df['left_int'] = [i[0] for i in conf]
    pred_df['right_int'] = [i[1] for i in conf]
    new_days = pd.DataFrame(7 * [0], columns=['adj close'], index=add_dates)
    data = pd.concat([data, new_days])

    back = 30
    prev_week = df[-back:]
    prev_week['prediction'] = back*[None]
    prev_week['left_int'] = back*[None]
    prev_week['right_int'] = back*[None]
    prev_week = prev_week.rename(columns={'Adj Close': 'history'})
    prev_week = prev_week[['prediction', 'left_int', 'right_int', 'history']]
    prev_week.index = prev_week.index.strftime('%Y-%m-%d')
    plt_df = pd.concat([prev_week, pred_df])
    return plt_df


async def plot_predict(data):
    plt.figure()
    plt.plot(data[['history', 'prediction']])
    plt.fill_between(x=data.index, y1=data['left_int'], y2=data['right_int'], color='b', alpha=.1)
    plt.legend(['history', 'prediction'])
    plt.xticks(rotation=90)
    plt.tick_params(axis="x", labelsize=6)
    plt.title(f"Прогноз на неделю")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    file = BufferedInputFile(buf.read(), filename="predict_price.png")
    return file


class Form(StatesGroup):
    time_range = State()


@dp.message(Command('start'))
async def welcome(message: types.Message, state: FSMContext) -> None:
    kb = [
        [types.KeyboardButton(text="Динамика стоимости")],
        [types.KeyboardButton(text="Предсказание на следующую неделю")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Жми!!!"
    )
    await message.answer("Выбери одну из кнопок:", reply_markup=keyboard)


@dp.message(F.text.lower() == "динамика стоимости")
async def get_range_date(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Form.time_range)
    await message.reply("Введите временной интервал для построения графика в формате YYYY-MM-DD YYYY-MM-DD (например, "
                        "2023-01-01 2023-12-31):",
                        reply_markup=types.ReplyKeyboardRemove())

# Акции
TICKERS = ['BTC-USD']
# Колонка для парсинга с yfinance
COL_VALUE = 'Adj Close'


@dp.message(Form.time_range)
async def send_stock_history(message: types.Message, state: FSMContext):
    # Получить временной промежуток
    time_range = await state.update_data(time_range=message.text)

    start_date, end_date = time_range['time_range'].split()
    await state.clear()
    try:
        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        print(data)
        image = await plot_history(data, TICKERS)
        print(image)
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")


@dp.message(F.text.lower() == "предсказание на следующую неделю")
async def predict_next_week(message: types.Message):
    # await message.reply("В разработке",
    #                     reply_markup=types.ReplyKeyboardRemove())

    try:
        data, df = await data_loader()
        plt_df = await predict(data, df)

        file = await plot_predict(plt_df)
        await bot.send_photo(message.chat.id, photo=file)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")


# Start polling
async def main():
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await dp.storage.close()


if __name__ == '__main__':
    asyncio.run(main())
