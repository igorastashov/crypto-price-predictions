import unittest
from unittest.mock import MagicMock, AsyncMock, patch, ANY, call
from aiogram import types
from app import welcome, get_name_ticker, get_find_ticker, send_stock_history
from app import get_name_ticker_01, get_find_ticker_01, send_crypto_avg


from app import Form
from pre_processing import data_loader
from plots import plot_history

import pandas as pd
from aiogram.filters.state import State, StatesGroup


class TestWelcome(unittest.IsolatedAsyncioTestCase):
    @patch("app.types.Message")
    async def test_welcome_message(self, mock_message):
        message_instance = mock_message.return_value
        message_instance.answer = AsyncMock()

        await welcome(message_instance)

        message_instance.answer.assert_called_once_with(
            "Выбери одну из кнопок:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Динамика стоимости")],
                    [types.KeyboardButton(text="Динамика среднемесячной стоимости")],
                    [types.KeyboardButton(text="Представление стоимости в виде торговых свечей")],
                    [types.KeyboardButton(text="Предсказание на будущее")],
                    [types.KeyboardButton(text="Оставить отзыв")],
                ],
                resize_keyboard=True,
                input_field_placeholder="Жми!!!",
            )
        )


class TestGetNameTicker(unittest.IsolatedAsyncioTestCase):
    @patch("app.types.Message")
    async def test_get_name_ticker_handler(self, mock_message):
        mock_message.text = "Динамика стоимости"
        mock_message.answer = AsyncMock()

        # Создаем дополнительный мок-объект для текстового условия F.text.lower() == "динамика стоимости"
        with patch("app.F") as mock_F:
            mock_F.text.lower.return_value = "динамика стоимости"

            await get_name_ticker(mock_message)

            # Проверяем, что функция answer была вызвана с ожидаемыми параметрами, используя ANY для reply_markup
            mock_message.answer.assert_called_once_with(
                "Выберите монету:",
                reply_markup=ANY
            )


class TestGetFindTicker(unittest.IsolatedAsyncioTestCase):
    @patch("app.types.CallbackQuery")
    @patch("app.FSMContext")
    @patch("app.bot")
    async def test_get_find_ticker_handler(self, mock_bot, mock_fsm_context, mock_callback_query):
        test_cases = [
            ("BTC-USD", "Вы выбрали BTC-USD."),
            ("ETH-USD", "Вы выбрали ETH-USD.")
        ]
        for selected_coin, expected_message in test_cases:
            callback_instance = mock_callback_query.return_value
            callback_instance.data = selected_coin
            callback_instance.from_user.id = 123456789  # Пример ID пользователя

            # Мокируем методы bot.answer_callback_query, bot.send_message и state.update_data
            mock_bot.answer_callback_query = AsyncMock()
            mock_bot.send_message = AsyncMock()
            mock_fsm_context.update_data = AsyncMock()
            mock_fsm_context.set_state = AsyncMock()

            await get_find_ticker(callback_instance, mock_fsm_context)

            # Проверяем, что функция answer_callback_query была вызвана с ожидаемыми параметрами
            mock_bot.answer_callback_query.assert_called_once_with(callback_instance.id)

            # Проверяем, что функция update_data была вызвана с ожидаемыми параметрами
            mock_fsm_context.update_data.assert_called_once_with(coin=selected_coin)

            # Проверяем, что функция set_state была вызвана с ожидаемыми параметрами
            mock_fsm_context.set_state.assert_called_once_with(ANY)

            # Проверяем, что функция send_message была вызвана с ожидаемыми параметрами
            expected_calls = [
                call(callback_instance.from_user.id, f"Вы выбрали {selected_coin}."),
                call(callback_instance.from_user.id, "Введите временной интервал для построения графика в формате: "
                                                      "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):")
            ]
            mock_bot.send_message.assert_has_calls(expected_calls, any_order=False)


class TestSendStockHistory(unittest.IsolatedAsyncioTestCase):
    @patch("pre_processing.data_loader", new_callable=AsyncMock)
    @patch("plots.plot_history", new_callable=AsyncMock)
    @patch("app.bot", new_callable=AsyncMock)
    async def test_send_stock_history_success(self, mock_bot, mock_data_loader, mock_plot_history):

        # Устанавливаем состояние
        state = AsyncMock()

        async def async_update_data(*args, **kwargs):
            return {"time_range": "2023-01-01 2023-12-31"}

        state.update_data = AsyncMock(side_effect=async_update_data)

        # Задаем сообщение от пользователя
        message = MagicMock()

        async def async_reply(*args, **kwargs):
            pass

        message.reply = AsyncMock(side_effect=async_reply)
        message.text = "2023-01-01 2023-12-31"  # Устанавливаем текст сообщения
        message.chat.id = 123456789  # Пример ID чата

        # Устанавливаем ожидаемый результат загрузки данных
        data_sample = pd.DataFrame({"Date": ['2024-01-01', '2024-01-02', '2024-02-03'],
                                    "BTC-USD": [10, 20, 30]}).set_index('Date', inplace=False)

        mock_data_loader.return_value = data_sample

        try:
            # Вызываем тестируемую функцию
            await send_stock_history(message, state)
        except Exception as e:
            print(f"An exception occurred: {e}")

    async def test_invalid_time_range_format(self):
        # Устанавливаем состояние
        state = AsyncMock()

        async def async_update_data(*args, **kwargs):
            return {"time_range": "invalid_time_range_format"}

        state.update_data = AsyncMock(side_effect=async_update_data)

        # Задаем сообщение от пользователя
        message = MagicMock()

        async def async_reply(*args, **kwargs):
            pass

        message.reply = AsyncMock(side_effect=async_reply)
        message.text = "invalid_time_range_format"  # Неправильный формат временного интервала

        # Вызываем тестируемую функцию
        await send_stock_history(message, state)

        # Проверяем, что отправлено сообщение об ошибке
        message.reply.assert_called_once_with("Неверный формат временного интервала. Попробуй все заново.")


class TestGetNameTicker01(unittest.IsolatedAsyncioTestCase):
    @patch("app.types.Message")
    async def test_get_name_ticker_01_handler(self, mock_message):
        mock_message.text = "Динамика среднемесячной стоимости"
        mock_message.answer = AsyncMock()

        with patch("app.F") as mock_F:
            mock_F.text.lower.return_value = "динамика среднемесячной стоимости"

            await get_name_ticker_01(mock_message)

            mock_message.answer.assert_called_once_with(
                "Выберите монету:",
                reply_markup=ANY
            )


class TestGetFindTicker01(unittest.IsolatedAsyncioTestCase):
    @patch("app.types.CallbackQuery")
    @patch("app.FSMContext")
    @patch("app.bot")
    async def test_get_find_ticker_01_handler(self, mock_bot, mock_fsm_context, mock_callback_query):
        test_cases = [
            ("BTC-USD avg", "BTC-USD"),
            ("ETH-USD avg", "ETH-USD")
        ]
        for selected_coin, expected_message in test_cases:
            callback_instance = mock_callback_query.return_value
            callback_instance.data = selected_coin
            callback_instance.from_user.id = 123456789  # Пример ID пользователя

            # Мокируем методы bot.answer_callback_query, bot.send_message и state.update_data
            mock_bot.answer_callback_query = AsyncMock()
            mock_bot.send_message = AsyncMock()
            mock_fsm_context.update_data = AsyncMock()
            mock_fsm_context.set_state = AsyncMock()

            await get_find_ticker_01(callback_instance, mock_fsm_context)

            # Проверяем, что функция answer_callback_query была вызвана с ожидаемыми параметрами
            mock_bot.answer_callback_query.assert_called_once_with(callback_instance.id)

            # Проверяем, что функция update_data была вызвана с ожидаемыми параметрами
            mock_fsm_context.update_data.assert_called_once_with(coin=selected_coin)

            # Проверяем, что функция set_state была вызвана с ожидаемыми параметрами
            mock_fsm_context.set_state.assert_called_once_with(ANY)

            # Проверяем, что функция send_message была вызвана с ожидаемыми параметрами
            expected_calls = [
                call(callback_instance.from_user.id, f"Вы выбрали {expected_message}."),
                call(callback_instance.from_user.id, "Введите временной интервал для построения графика средней стоимости в формате: "
                                                            "YYYY-MM-DD YYYY-MM-DD (например, 2023-01-01 2023-12-31):")
            ]
            mock_bot.send_message.assert_has_calls(expected_calls, any_order=False)


class TestSendCryptoAvg(unittest.IsolatedAsyncioTestCase):
    @patch("pre_processing.data_loader", new_callable=AsyncMock)
    @patch("plots.viz_avg", new_callable=AsyncMock)
    @patch("app.bot", new_callable=AsyncMock)
    async def test_send_stock_history_success(self, mock_bot, mock_data_loader, mock_plot_history):

        # Устанавливаем состояние
        state = AsyncMock()

        async def async_update_data(*args, **kwargs):
            return {"time_ranger": "2023-01-01 2023-12-31"}

        state.update_data = AsyncMock(side_effect=async_update_data)

        # Задаем сообщение от пользователя
        message = MagicMock()

        async def async_reply(*args, **kwargs):
            pass

        message.reply = AsyncMock(side_effect=async_reply)
        message.text = "2023-01-01 2023-12-31"  # Устанавливаем текст сообщения
        message.chat.id = 123456789  # Пример ID чата

        # Устанавливаем ожидаемый результат загрузки данных
        data_sample = pd.DataFrame({"Date": ['2024-01-01', '2024-01-02', '2024-02-03'],
                                    "BTC-USD": [10, 20, 30]}).set_index('Date', inplace=False)

        mock_data_loader.return_value = data_sample

        try:
            # Вызываем тестируемую функцию
            await send_crypto_avg(message, state)
        except Exception as e:
            print(f"An exception occurred: {e}")

    async def test_invalid_time_range_format(self):
        # Устанавливаем состояние
        state = AsyncMock()

        async def async_update_data(*args, **kwargs):
            return {"time_ranger": "invalid_time_range_format"}

        state.update_data = AsyncMock(side_effect=async_update_data)

        # Задаем сообщение от пользователя
        message = MagicMock()

        async def async_reply(*args, **kwargs):
            pass

        message.reply = AsyncMock(side_effect=async_reply)
        message.text = "invalid_time_range_format"  # Неправильный формат временного интервала

        # Вызываем тестируемую функцию
        await send_crypto_avg(message, state)

        # Проверяем, что отправлено сообщение об ошибке
        message.reply.assert_called_once_with("Неверный формат временного интервала. Попробуй все заново.")



if __name__ == "__main__":
    unittest.main()
