import json
import asyncio
# import base64
import logging
# import time
from datetime import datetime, timedelta
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from imapclient import IMAPClient
from email import message_from_bytes
from io import BytesIO
import openpyxl
from pytz import timezone

# Настройки логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки
BOT_TOKEN = '7103569564:AAHQUnfhiIj8yoRgRpDsuazPaVC3leaX9s4'
IMAP_SERVER = 'imap.yandex.com'
EMAIL_USER = 'rn-cardmail@yandex.ru'
EMAIL_PASS = 'bmrirqolilipxstq'
TELEGRAM_CHAT_ID = '877804669'
CHECK_INTERVAL = 1800  # Период опроса (в секундах)
IMAP_PORT = 993

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Пример с использованием часового пояса, замените 'Europe/Moscow' на ваш часовой пояс
tz = timezone('Europe/Moscow')  # Замените на ваш часовой пояс


async def check_email():
    while True:
        try:
            logger.info("Подключение к почтовому ящику...")
            with IMAPClient(IMAP_SERVER, port=IMAP_PORT, ssl=True) as client:
                client.login(EMAIL_USER, EMAIL_PASS)
                logger.info("Успешный вход в почтовый ящик.")
                client.select_folder('INBOX')

                # Поиск писем, начиная с сегодняшнего дня
                last_30_min = tz.localize(datetime.now() - timedelta(minutes=30))
                messages = client.search(['SINCE', last_30_min.strftime('%d-%b-%Y')])

                logger.info(f"Найдено сообщений с сегодняшнего дня: {len(messages)}")

                for uid, message_data in client.fetch(messages, 'RFC822').items():
                    email_message = message_from_bytes(message_data[b'RFC822'])
                    email_date = email_message['Date']

                    # Преобразование даты письма и фильтрация по времени
                    email_datetime = datetime.strptime(email_date, '%a, %d %b %Y %H:%M:%S %z')
                    if email_datetime >= last_30_min:
                        logger.info(f"Обработка сообщения UID {uid} с темой: {email_message['subject']}")

                        if email_message.is_multipart():
                            for part in email_message.walk():
                                content_type = part.get_content_type()
                                logger.info(f"Найдено вложение с типом: {content_type}")

                                if content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                                    'application/vnd.ms-excel', 'application/octet-stream']:
                                    file_data = part.get_payload(decode=True)
                                    await process_excel(file_data)
                                    client.add_flags(uid, '\\Seen')
                                    logger.info(f"Сообщение UID {uid} обработано.")
                        else:
                            logger.info(f"Сообщение UID {uid} не является multipart и не содержит вложений.")
            logger.info("Проверка завершена.")
        except Exception as e:
            logger.error(f"Ошибка при проверке почты: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


async def process_excel(file_data):
    logger.info("Начало обработки Excel-файла.")
    try:
        # Загружаем Excel-файл в DataFrame
        df = pd.read_excel(BytesIO(file_data), dtype=str)  # Приводим к строкам, чтобы избежать NaN
        df.dropna(how='all', inplace=True)  # Удаляем полностью пустые строки
        df.dropna(axis=1, how='all', inplace=True)  # Удаляем полностью пустые столбцы

        logger.info(f"Excel-файл успешно прочитан, содержит {df.shape[0]} строк и {df.shape[1]} столбцов.")

        # Фильтруем строки с нужными данными (например, проверка заполненности столбцов)
        filtered_rows = df[df.iloc[:, 0].notna() & df.iloc[:, 1].notna() & df.iloc[:, -2].notna()]

        # Преобразование в JSON
        json_data = filtered_rows.to_json(orient='records', force_ascii=False, indent=2)

        # Загрузка данных из JSON
        data = json.loads(json_data)

        # Извлечение заголовков (первый элемент)
        headers = list(data[0].values())

        # Извлечение значений (второй элемент)
        values = list(data[1].values())

        # Создание словаря с заголовками в качестве ключей и значениями в качестве значений
        result_dict = dict(zip(headers, values))

        # Преобразование в красиво отформатированный JSON
        pretty_json = json.dumps(result_dict, ensure_ascii=False, indent=2)

        logger.info(f"Данные для отправки: {pretty_json}")

        # Отправка JSON в Telegram
        await bot.send_message(TELEGRAM_CHAT_ID, f"<pre>{pretty_json}</pre>", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при обработке Excel-файла: {e}")


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply("Бот запущен и будет проверять новые письма.")


async def main():
    await asyncio.create_task(check_email())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
