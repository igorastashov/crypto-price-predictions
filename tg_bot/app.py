import asyncio
import logging
import os
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from models import arima_model
from plots import plot_history, plot_predict, viz_avg, viz_candle
from post_processing import get_data_for_plot, post_processing_data
from pre_processing import data_loader, data_grp, data_all

load_dotenv()

# Колонка для парсинга с yfinance
COL_VALUE = "Adj Close"

# Последнее кол-во дней для отображения на графике совместно с предсказанием
BACK_DAYS = 15

# Прогноз криптовалют
TICKERS_PREDICT = []

# Тикеры криптовалют
TICKERS = []

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


class Form(StatesGroup):
    coin = State()
    time_range = State()
    time_ranger = State()
    time_rangers = State()
    horizon_predict = State()
    review = State()
    expect = State()


@dp.message(Command("start"))
async def welcome(message: types.Message) -> None:
    kb = [
        [types.KeyboardButton(text="Динамика стоимости")],
        [types.KeyboardButton(text="Динамика среднемесячной стоимости")],
        [types.KeyboardButton(text="Представление стоимости в виде торговых свечей")],
        [types.KeyboardButton(text="Предсказание на будущее")],
        [types.KeyboardButton(text="Оставить отзыв")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, input_field_placeholder="Жми!!!"
    )
    await message.answer("Выбери одну из кнопок:", reply_markup=keyboard)


@dp.message(F.text.lower() == "динамика стоимости")
async def get_name_ticker(message: types.Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="BTC-USD", callback_data="BTC-USD"))

    builder.add(types.InlineKeyboardButton(text="ETH-USD", callback_data="ETH-USD"))
    await message.answer("Выберите монету:", reply_markup=builder.as_markup())


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
    await bot.send_message(
        callback.from_user.id,
        "Введите временной интервал для построения графика в формате: "
        "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):",
    )


#История цен на криптовалюты

@dp.message(Form.time_range)
async def send_stock_history(message: types.Message, state: FSMContext):
    """
    Отправляет историю цен на криптовалюты
     в указанном временном диапазоне в виде графика.

    :param message: Объект сообщения,
     содержащий время начала и конца временного диапазона.
    :param state: Состояние конечного автомата для управления состоянием бота.
    :return: Отравка сообщения в виде графика

    Исключения:
    Если произошла ошибка при загрузке данных или построении графика,
    будет отправлено сообщение с описанием ошибки пользователю.
    """
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$")

    time_range = await state.update_data(time_range=message.text)
    if not pattern.match(time_range["time_range"]):
        await message.reply(
            "Неверный формат временного интервала. Попробуй все заново."
        )
        return

    start_date, end_date = time_range["time_range"].split()

    await state.clear()
    try:
        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        image = await plot_history(data, TICKERS)
        TICKERS.pop()
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    await state.set_state(Form.expect)



#Формирует среднемесячную стоимость крипт. в заданном временном интервале
    
@dp.message(F.text.lower() == "динамика среднемесячной стоимости")
async def get_name_ticker_01(message: types.Message) -> None:
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="BTC-USD avg", callback_data="BTC-USD avg"))
    builder.add(types.InlineKeyboardButton(text="ETH-USD avg", callback_data="ETH-USD avg"))
    
    await message.answer("Выберите монету:", reply_markup=builder.as_markup())


@dp.callback_query(lambda query: query.data in ["BTC-USD avg", "ETH-USD avg"])
async def get_find_ticker_01(callback: types.CallbackQuery, state: FSMContext):
    selected_coin = callback.data
    TICKERS.append(selected_coin[:-4])

    await bot.answer_callback_query(callback.id)
    await state.update_data(coin=selected_coin)

    if selected_coin == "BTC-USD avg":
        await bot.send_message(callback.from_user.id, "Вы выбрали BTC-USD.")

    elif selected_coin == "ETH-USD avg":
        await bot.send_message(callback.from_user.id, "Вы выбрали ETH-USD.")

    await state.set_state(Form.time_ranger)
    await bot.send_message(
        callback.from_user.id,
        "Введите временной интервал для построения графика средней стоимости в формате: "
        "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):",
    )


@dp.message(Form.time_ranger)
async def send_crypto_avg(message: types.Message, state: FSMContext):
    """
    Отправляет историю цен  средней стоимости криптовалют
     в указанном временном диапазоне в виде графика

    """
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$")

    time_ranger = await state.update_data(time_ranger=message.text)
    if not pattern.match(time_ranger["time_ranger"]):
        await message.reply(
            "Неверный формат временного интервала." " Попробуй все заново."
        )
        return

    start_date, end_date = time_ranger["time_ranger"].split()

    await state.clear()
    try:

        data = await data_loader(start_date, end_date, TICKERS, COL_VALUE)
        data_gr = await data_grp(data,TICKERS)
        image = await viz_avg(data_gr, TICKERS)
        TICKERS.pop()
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    await state.set_state(Form.expect)



#Показывает динамику стоимости криптовалют в виде свечного графика
    
@dp.message(F.text.lower() == "представление стоимости в виде торговых свечей")
async def get_name_ticker_02(message: types.Message) -> None:
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="BTC-USD candle", callback_data="BTC-USD candle"))
    builder.add(types.InlineKeyboardButton(text="ETH-USD candle", callback_data="ETH-USD candle"))
    
    await message.answer("Выберите монету:", reply_markup=builder.as_markup())


@dp.callback_query(lambda query: query.data in ["BTC-USD candle", "ETH-USD candle"])
async def get_find_ticker_02(callback: types.CallbackQuery, state: FSMContext):
    selected_coin = callback.data
    TICKERS.append(selected_coin[:-7])

    await bot.answer_callback_query(callback.id)
    await state.update_data(coin=selected_coin)

    if selected_coin == "BTC-USD candle":
        await bot.send_message(callback.from_user.id, "Вы выбрали BTC-USD.")

    elif selected_coin == "ETH-USD candle":
        await bot.send_message(callback.from_user.id, "Вы выбрали ETH-USD.")

    await state.set_state(Form.time_rangers)
    await bot.send_message(
        callback.from_user.id,
        "Введите временной интервал для построения свечного графика стоимости в формате: "
        "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):",
    )


@dp.message(Form.time_rangers)
async def send_crypto_candle(message: types.Message, state: FSMContext):
    """
    Отправляет представление криптовалют
     в указанном временном диапазоне в виде свечного графика.

    """
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$")

    time_rangers = await state.update_data(time_rangers=message.text)
    if not pattern.match(time_rangers["time_rangers"]):
        await message.reply(
            "Неверный формат временного интервала. Попробуй все заново."
        )
        return

    start_date, end_date = time_rangers["time_rangers"].split()

    await state.clear()
    try:

        data = await data_all(start_date, end_date, TICKERS)
        image = await viz_candle(data)
        TICKERS.pop()
        await bot.send_photo(message.chat.id, photo=image)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    await state.set_state(Form.expect)


#Прогноз с помощью алгоритма ARIMA на криатовалюты

@dp.message(F.text.lower() == "предсказание на будущее")
async def get_name_ticker_predict(message: types.Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="BTC-USD", callback_data="BTC-USD_predict")
    )

    builder.add(
        types.InlineKeyboardButton(text="ETH-USD", callback_data="ETH-USD_predict")
    )
    await message.answer("Выберите монету:", reply_markup=builder.as_markup())


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
    await bot.send_message(
        callback.from_user.id,
        "Введите число,"
        " соответствующее количеству дней для предсказания (например, 7):",
    )


@dp.message(Form.horizon_predict)
async def predict_next_days(message: types.Message, state: FSMContext):
    """
    Прогноз стоимости криптовалют в виде графика на следующий период времени.

    """
    # Время начала рассмотрения данных
    start_date = "2023-01-01"
    # Время окончания рассмотрения данных
    end_date = datetime.now()

    if not message.text.isdigit():
        await message.reply(
            "Пожалуйста,"
            " введите корректное число дней для предсказания (целое число)."
        )
        return

    # Горизонт предсказаний
    horizon_predict = await state.update_data(horizon_predict=message.text)
    horizon_predict = int(horizon_predict["horizon_predict"])

    try:
        data = await data_loader(start_date, end_date, TICKERS_PREDICT, COL_VALUE)
        predict_model, conf = await arima_model(
            data, TICKERS_PREDICT[0], horizon_predict
        )
        predict_df = await post_processing_data(
            predict_model, end_date, horizon_predict, conf
        )
        concat_data = await get_data_for_plot(
            data, BACK_DAYS, TICKERS_PREDICT[0], predict_df
        )
        image = await plot_predict(concat_data)
        await bot.send_photo(message.chat.id, photo=image)
        TICKERS_PREDICT.pop()
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

    horizon_predict = None
    await state.update_data(horizon_predict=None)
    await state.update_data(coin=None)
    await state.set_state(Form.expect)



# Реализация логики оставления отзыва 
    
@dp.message(F.text.lower() == "оставить отзыв")
async def get_callback(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Приложение отличное!", callback_data="good")
    )
    builder.add(
        types.InlineKeyboardButton(text="Приложение ужасное!", callback_data="bed")
    )
    await message.answer(
        text="Ваша оценка приложения?:", reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda query: query.data in ["good", "bed"])
async def get_feedback(callback: types.CallbackQuery, state: FSMContext):
    review = callback.data
    if review == "good":
        await callback.answer(text="Увидимся снова!", show_alert=True)
    elif review == "bed":
        await callback.answer(text="Больше не увидимся!", show_alert=True)
    await state.set_state(Form.expect)


# Start polling
async def main():
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await dp.storage.close()


if __name__ == "__main__":
    asyncio.run(main())
