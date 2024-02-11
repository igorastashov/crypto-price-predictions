##  Прогнозирование стоимости криптовалюты


Асташов И.В., Юсупов Ш.Ш., 2024.

Репозиторий содержит проект с реализованным чат-ботом при помощи асинхронной библиотеки aiogram, который прогнозирует стоимость криптовалюты в выбранном горизонте. 

Проект выполнен в рамках курса «Прикладной Python» магистерской программы НИУ ВШЭ 
[«Машинное обучение и высоконагруженные системы»](https://www.hse.ru/ma/mlds/).

## (1) Файлы

- tg_bot/app.py: файл приложения telegram-bot
- tg_bot/models.py: модель ARIMA 
- tg_bot/plots.py:функции визуализации
- tg_bot/pre_processing.py: функции загрузки и предобработки данных
- tg_bot/post_processing.py: функции обработки предсказанных моделью данных
- .env: файл с токеном для бота
- requirements.txt: файл зависимостей

## (2) Запуск локально

### Shell

Для прямого запуска telegram-bot локально:

```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python tg_bot/app.py
```
Открыть в Telegram [crypto_price_predictions_bot](https://t.me/crypto_price_predictions_bot) для просмотра функционала. Ввести `/start`.

## (A) Благодарности

Используемые материалы: [https://mastergroosha.github.io/aiogram-3-guide/](https://mastergroosha.github.io/aiogram-3-guide/),
[Лекции HSE](https://www.youtube.com/watch?v=m_M8T7xr9MU&list=PLmA-1xX7IuzADGz3hSgPPm6ib11Z0HSML&index=7).

