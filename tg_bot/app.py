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

import re


# Колонка для парсинга с yfinance
COL_VALUE = 'Adj Close'

# Последнее кол-во дней для отображения на графике совместно с предсказанием
BACK_DAYS = 15

# Акции для предсказания
TICKERS_PREDICT = []

# Акции
TICKERS = []


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
    horizon_predict = State()
    review = State()
    expect = State()


@dp.message(Command('start'))
async def welcome(message: types.Message) -> None:
    kb = [
        [types.KeyboardButton(text="Динамика стоимости")],
        [types.KeyboardButton(text="Предсказание на будущее")],
        [types.KeyboardButton(text="Оставить отзыв")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Жми!!!"
    )
    await message.answer("Выбери одну из кнопок:", reply_markup=keyboard)


@dp.message(F.text.lower() == "динамика стоимости")
async def get_name_ticker(message: types.Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="BTC-USD",
        callback_data="BTC-USD")
    )

    builder.add(types.InlineKeyboardButton(
        text="ETH-USD",
        callback_data="ETH-USD")
    )
    await message.answer(
        "Выберите монету:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda query: query.data in ["BTC-USD", "ETH-USD"])
async def get_find_ticker(callback: types.CallbackQuery, state: FSMContext):
    selected_coin = callback.data
    TICKERS.append(selected_coin)

    await bot.answer_callback_query(callback.id)
    await state.update_data(coin=selected_coin)

    if selected_coin == "BTC-USD":
        await bot.send_message(callback.from_user.id, "Вы выбрали BTC-USD.")

    elif selected_coin == "ETH-USD":
        await bot.send_message(callback.from_user.id, "Вы выбрали ETH-USD.")

    await state.set_state(Form.time_range)
    await bot.send_message(callback.from_user.id, "Введите временной интервал для построения графика в формате: "
                                                  "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):"
                           )


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
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$')

    time_range = await state.update_data(time_range=message.text)
    print(time_range['time_range'])
    if not pattern.match(time_range['time_range']):
        await message.reply("Неверный формат временного интервала. Попробуй все заново")
        return

    start_date, end_date = time_range['time_range'].split()

    await state.clear()
    try:
        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        image = await plot_history(data, TICKERS)
        TICKERS.pop()
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    await state.set_state(Form.expect)


@dp.message(F.text.lower() == "предсказание на будущее")
async def get_name_ticker_predict(message: types.Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="BTC-USD",
        callback_data="BTC-USD_predict")
    )

    builder.add(types.InlineKeyboardButton(
        text="ETH-USD",
        callback_data="ETH-USD_predict")
    )
    await message.answer(
        "Выберите монету:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda query: query.data in ["BTC-USD_predict", "ETH-USD_predict"])
async def get_find_ticker_predict(callback: types.CallbackQuery, state: FSMContext):
    selected_coin = callback.data
    TICKERS_PREDICT.append(selected_coin[:-8])

    await bot.answer_callback_query(callback.id)
    await state.update_data(coin=selected_coin)

    if selected_coin == "BTC-USD_predict":
        await bot.send_message(callback.from_user.id, "Вы выбрали BTC-USD.")

    elif selected_coin == "ETH-USD_predict":
        await bot.send_message(callback.from_user.id, "Вы выбрали ETH-USD.")

    await state.set_state(Form.horizon_predict)
    await bot.send_message(callback.from_user.id, "Введите число, соответствующее количеству дней для предсказания (например, 7):"
                           )


@dp.message(Form.horizon_predict)
async def predict_next_days(message: types.Message, state: FSMContext):
    """
    Вывод предсказания стоимости в виде графика на следующий период времени.

    :param state:
    :param message: Объект сообщения, намерение совершить предсказание на следующий период времени;
    :return: Отравка сообщения в виде графика.
    """
    # Время начала рассмотрения данных
    start_date = '2023-01-01'
    # Время окончания рассмотрения данных
    end_date = datetime.now()

    if not message.text.isdigit():
        await message.reply("Пожалуйста, введите корректное число дней для предсказания (целое число).")
        return

    # Горизонт предсказаний
    horizon_predict = await state.update_data(horizon_predict=message.text)
    horizon_predict = int(horizon_predict['horizon_predict'])

    try:
        data = await data_loader(start_date, end_date, TICKERS_PREDICT, COL_VALUE)
        predict_model, conf = await arima_model(data, TICKERS_PREDICT[0], horizon_predict)
        predict_df = await post_processing_data(predict_model, end_date, horizon_predict, conf)
        concat_data = await get_data_for_plot(data, BACK_DAYS, TICKERS_PREDICT[0], predict_df)
        image = await plot_predict(concat_data)
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    await state.set_state(Form.expect)


@dp.message(F.text.lower() == "оставить отзыв")
async def get_callback(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Приложение отличное!",
        callback_data="good")
    )
    builder.add(types.InlineKeyboardButton(
        text="Приложение ужасное!",
        callback_data="bed")
    )
    await message.answer(
        text="Ваша оценка приложения?:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda query: query.data in ["good", "bed"])
async def get_feedback(callback: types.CallbackQuery, state: FSMContext):
    review = callback.data
    if review == "good":
        await callback.answer(
            text="Увидимся снова!",
            show_alert=True
        )
    elif review == "bed":
        await callback.answer(
            text="Больше не увидимся!",
            show_alert=True
        )
    await state.set_state(Form.expect)


# Start polling
async def main():
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await dp.storage.close()


if __name__ == '__main__':
    asyncio.run(main())
