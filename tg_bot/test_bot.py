import unittest
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from aiogram import types
from app import welcome, get_name_ticker


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


if __name__ == "__main__":
    unittest.main()
