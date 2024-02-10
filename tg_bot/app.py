import asyncio
import logging

from aiogram import types
from datetime import datetime

from aiogram.filters.state import State, StatesGroup

from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, F

from pre_processing import data_loader
from plots import plot_history, plot_predict
from models import arima_model
from post_processing import post_processing_data, get_data_for_plot

from aiogram.utils.keyboard import InlineKeyboardBuilder


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "6879124162:AAEOc-Fs1zejw552nMZM-DiYorjJk6OFr5U"
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


class Form(StatesGroup):
    coin = State()
    time_range = State()


@dp.message(Command('start'))
async def welcome(message: types.Message) -> None:
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
async def get_name_ticker(message: types.Message, state: FSMContext) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="BTC-USD",
        callback_data="btc_usd")
    )

    builder.add(types.InlineKeyboardButton(
        text="ETH-USD",
        callback_data="eth_usd")
    )
    await message.answer(
        "Выберите монету:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda query: query.data in ["btc_usd", "eth_usd"])
async def get_find_ticker(callback: types.CallbackQuery, state: FSMContext):
    selected_coin = callback.data
    await bot.answer_callback_query(callback.id)
    await state.update_data(coin=selected_coin)

    if selected_coin == "btc_usd":
        await bot.send_message(callback.from_user.id, "Вы выбрали BTC-USD.")

    elif selected_coin == "eth_usd":
        await bot.send_message(callback.from_user.id, "Вы выбрали ETH-USD.")

    await state.set_state(Form.time_range)
    await bot.send_message(callback.from_user.id, "Введите временной интервал для построения графика в формате YYYY-MM-DD YYYY-MM-DD (например, \"2023-01-01 2023-12-31\"):")

# Акции
TICKERS = ['BTC-USD']
# Колонка для парсинга с yfinance
COL_VALUE = 'Adj Close'


@dp.message(Form.time_range)
async def send_stock_history(message: types.Message, state: FSMContext):
    """
    Отправляет историю цен на акции в указанном временном диапазоне в виде графика.

    :param message: Объект сообщения, содержащий время начала и конца временного диапазона.
    :param state: Состояние конечного автомата для управления состоянием бота.
    :return: Отравка сообщения в виде графика

    Исключения:
    Если произошла ошибка при загрузке данных или построении графика,
    будет отправлено сообщение с описанием ошибки пользователю.
    """
    time_range = await state.update_data(time_range=message.text)
    start_date, end_date = time_range['time_range'].split()
    await state.clear()
    try:
        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        image = await plot_history(data, TICKERS)
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")


# Горизонт предсказаний
PERIODS = 7

# Последнее кол-во дней для отображения на графике совместно с предсказанием
BACK_DAYS = 15


@dp.message(F.text.lower() == "предсказание на следующую неделю")
async def predict_next_days(message: types.Message):
    """
    Вывод предсказания стоимости в виде графика на следующий период времени.

    :param message: Объект сообщения, намерение совершить предсказание на следующий период времени;
    :return: Отравка сообщения в виде графика.
    """
    # Время начала рассмотрения данных
    start_date = '2023-01-01'
    # Время окончания рассмотрения данных
    end_date = datetime.now()

    try:
        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        predict_model, conf = await arima_model(data, TICKERS[0], PERIODS)
        predict_df = await post_processing_data(predict_model, end_date, PERIODS, conf)
        concat_data = await get_data_for_plot(data, BACK_DAYS, TICKERS[0], predict_df)
        image = await plot_predict(concat_data)
        await bot.send_photo(message.chat.id, photo=image)
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
