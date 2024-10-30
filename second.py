import json
import logging
import os
from datetime import datetime, timedelta

import requests
import schedule
import time
from dotenv import load_dotenv

load_dotenv('.env')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат с текущей датой и временем
    datefmt='%Y-%m-%d %H:%M:%S'  # Формат даты и времени
)

def fetch_and_send_transactions():
    # Параметры для API
    # begin = '2024-10-30T00:00:00'  # формат даты: YYYY-MM-DDTHH:MM:SS
    # end = '2024-10-30T23:59:59'
    # Вычисляем время начала и окончания (последние 3 часа)
    end_ = datetime.now()  # Текущее время
    begin_ = end_ - timedelta(hours=1)  # Вычитаем 3 часа

    # Форматируем даты в нужный формат
    begin = begin_.strftime('%Y-%m-%dT%H:%M:%S')
    end = end_.strftime('%Y-%m-%dT%H:%M:%S')
    base_url = 'https://lkapi.rn-card.ru/'  # Замените на ваш базовый URL сервера
    result_type = 'JSON'
    u = 'Kal9n'
    p = os.getenv('PASSWORD')
    contract = os.getenv('CONTRACT')

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

    # Проверка успешности запроса
    if response.status_code == 200:
        try:
            data = response.json()
            # # Сохранение ответа в файл
            # with open("response.json", "w", encoding="utf-8") as f:
            #     json.dump(data, f, indent=4, ensure_ascii=False)
            # print("Данные сохранены в файл response.json")

            # Извлечение списка операций
            operation_list: list = data.get('OperationList', [])

            # Сначала определяем список индексов для удаления
            indexes_to_remove = []

            # Обработка операций с возвратами
            for index, operation in enumerate(operation_list):
                ref_code = operation.get('Ref')
                if ref_code:  # Проверка, что Ref не пустой
                    ref_sum = operation.get('Sum', 0)
                    ref_value = operation.get('Value', 0)

                    for operation_2 in operation_list:
                        if operation_2.get('Code') == ref_code:
                            operation_2['Sum'] -= ref_sum  # Вычитаем сумму возврата
                            operation_2['Value'] -= ref_value
                            indexes_to_remove.append(index)  # Добавляем индекс для удаления
                            break

            # Удаляем операции по собранным индексам
            for index in sorted(indexes_to_remove, reverse=True):
                operation_list.pop(index)  # Удаляем операции возврата
            # Форматирование итогового списка операций для отправки

            # Отправка данных в Telegram
            TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')
            BOT_TOKEN = os.getenv('BOT_TOKEN')

            for operation in operation_list:
                formatted_date = datetime.strptime(operation.get('Date'), "%Y-%m-%dT%H:%M:%S").strftime(
                    "%d.%m.%Y %H:%M:%S")

                result_message = (f"<b>Код:</b> {operation['Code']}  \n"
                                  f"<b>Дата:</b> {formatted_date}  \n"
                                  f"<b>Держатель:</b> {operation.get('Holder')}  \n"
                                  f"<b>Сумма:</b> {operation['Sum']:.2f}  \n"
                                  "<i>-------------------------</i>")

                telegram_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                params = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': result_message,
                    'parse_mode': 'HTML'  # Для поддержки форматирования (например, жирный текст)
                }

                telegram_response = requests.post(telegram_url, data=params)
                if telegram_response.status_code == 200:
                    print("Сообщение успешно отправлено в Telegram.")
                else:
                    print(f"Ошибка при отправке сообщения в Telegram: {telegram_response.text}")
            logging.info('Ожидиние час')
        except json.JSONDecodeError:
            print("Ошибка: ответ не является JSON")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    else:
        print(f"Ошибка: {response.status_code}, ответ: {response.text}")


# Планирование задачи раз в 3 часа
schedule.every(1).hours.do(fetch_and_send_transactions)

# Первая отправка сразу
fetch_and_send_transactions()

# Запуск цикла планировщика
while True:
    schedule.run_pending()
    time.sleep(1)  # Задержка в 1 секунду между проверками
