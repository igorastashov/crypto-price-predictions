import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from aiogram.types import BufferedInputFile
import io


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "6879124162:AAEOc-Fs1zejw552nMZM-DiYorjJk6OFr5U"
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


async def generate_stock_graph():
    tickers = ['BTC-USD']
    start_date = '2023-01-01'
    end_date = datetime.now()

    stock_history = pd.concat((yf.download(ticker,
                                           start=start_date,
                                           end=end_date,
                                           interval='1h').assign(tkr=ticker) for ticker in tickers), ignore_index=False)

    # Create the graph
    plt.figure(figsize=(12, 5))
    plt.plot(stock_history['Adj Close'])
    plt.title(f'{tickers[0]} Stock Price History')
    plt.xlabel('Date')
    plt.ylabel('Price')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    file = BufferedInputFile(buf.read(), filename="stock_price_history.png")
    return file


@dp.message(Command('help'))
async def help_mode(message: types.Message):
    await message.answer('/history - график стоимости Bitcoin за все время\n')


@dp.message(Command('history'))
async def send_stock_history(message: types.Message):
    try:
        file = await generate_stock_graph()
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
