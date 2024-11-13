import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import requests
import schedule
import time

from database.engine import create_db, drop_db
from handlers import router

# Загрузка переменных из .env
load_dotenv('.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')
PASSWORD = os.getenv('PASSWORD')
CONTRACT = os.getenv('CONTRACT')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def fetch_and_send_transactions():
    end_ = datetime.now()
    begin_ = end_ - timedelta(hours=1)

    # Форматирование даты
    begin = begin_.strftime('%Y-%m-%dT%H:%M:%S')
    end = end_.strftime('%Y-%m-%dT%H:%M:%S')

    base_url = 'https://lkapi.rn-card.ru'
    result_type = 'JSON'
    u = 'Kal9n'
    p = PASSWORD
    contract = CONTRACT

    # Запрос на получение операций
    response = requests.get(
        url=f'{base_url}/api/emv/v2/GetOperByContract',
        params={
            'u': u,
            'p': p,
            'contract': contract,
            'begin': begin,
            'end': end,
            'type': result_type
        }
    )

    # Сохранение ответа в файл
    # with open("response.json", "w", encoding="utf-8") as f:
    #     json.dump(response.json(), f, indent=4, ensure_ascii=False)
    # print("Данные сохранены в файл response.json")

    # Проверка успешности запроса
    if response.status_code == 200:
        logging.info("Запрос выполнен успешно.")
        try:
            data = response.json()
            operation_list = data.get('OperationList', [])

            indexes_to_remove = []

            # Обработка возвратов
            for index, operation in enumerate(operation_list):
                ref_code = operation.get('Ref')
                code = operation.get('Code')
                if ref_code and ref_code != code:
                    ref_sum = operation.get('Sum', 0)
                    ref_value = operation.get('Value', 0)
                    for operation_2 in operation_list:
                        if operation_2.get('Code') == ref_code:
                            operation_2['Sum'] -= ref_sum
                            operation_2['Value'] -= ref_value
                            indexes_to_remove.append(index)
                            break

            # Удаление операций возврата
            for index in sorted(indexes_to_remove, reverse=True):
                operation_list.pop(index)

            # Форматирование и отправка данных в Telegram
            for operation in operation_list:
                if operation['GCat'] == 'FUEL':
                    formatted_date = datetime.strptime(operation.get('Date'), "%Y-%m-%dT%H:%M:%S").strftime(
                        "%d.%m.%Y %H:%M:%S")
                    result_message = (
                        f"<b>Код:</b> {operation['Code']}\n"
                        f"<b>Дата:</b> {formatted_date}\n"
                        f"<b>Держатель:</b> {operation.get('Holder')}\n"
                        f"<b>Сумма:</b> {operation['Sum']:.2f}\n"
                        f"<b>Топливо:</b> {operation.get('GName')}\n"
                        "<i>-------------------------</i>"
                    )
                    await bot.send_message(TELEGRAM_CHAT_ID, result_message, parse_mode='HTML')
            logging.info("Сообщения отправлены в Telegram.")
        except json.JSONDecodeError:
            logging.error("Ошибка: ответ не является JSON")
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
    else:
        logging.error(f"Ошибка: {response.status_code}, ответ: {response.text}")


async def schedule_transactions():
    # Планирование задачи каждую минуту
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(bot):
    # await drop_db()
    # await bot.set_webhook(url=f"{os.getenv('URL_APP')}")
    # webhook_info = await bot.get_webhook_info()
    # print(webhook_info)

    await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    # Удаление веб-хука перед использованием polling
    await bot.delete_webhook(drop_pending_updates=True)

    # Регистрация обработчиков команд
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Сначала выполните функцию сразу
    await fetch_and_send_transactions()

    # Запуск планировщика
    schedule.every(1).hours.do(lambda: asyncio.create_task(fetch_and_send_transactions()))

    # Запуск polling и планировщика транзакций параллельно
    await asyncio.gather(dp.start_polling(bot), schedule_transactions())


if __name__ == '__main__':
    asyncio.run(main())
