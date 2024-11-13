import json
import logging
import os
from datetime import datetime, timedelta

import requests
import schedule
import time
from dotenv import load_dotenv

load_dotenv('../.env')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат с текущей датой и временем
    datefmt='%Y-%m-%d %H:%M:%S'  # Формат даты и времени
)


def fetch_and_send_transactions(date_str):
    # Преобразуем строку даты в объект datetime
    date = datetime.strptime(date_str, '%d.%m.%y')

    # Устанавливаем начало и конец дня
    begin = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Форматируем даты в нужный формат
    begin_str = begin.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end.strftime('%Y-%m-%dT%H:%M:%S')

    # Здесь вы можете добавить код для получения и отправки транзакций
    print(f"Начало: {begin_str}, Конец: {end_str}")

    base_url = 'https://lkapi.rn-card.ru'
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

            # Извлечение списка операций
            operation_list: list = data.get('OperationList', [])
            # Сначала определяем список индексов для удаления
            indexes_to_remove = []

            # Обработка операций с возвратами
            for index, operation in enumerate(operation_list):
                ref_code = operation.get('Ref')
                code = operation.get('Code')
                if ref_code and ref_code != code:
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

                # Форматируем строку вывода
                result_message = (
                    f"{formatted_date} "
                    f"{str(operation['Sum']).replace('.', ',')} "  # Заменяем точку на запятую
                    f"{operation['Holder'].replace(' ', '-')} "
                    f"{operation['GName']} "
                )
                print(result_message)
                # telegram_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                # params = {
                #     'chat_id': TELEGRAM_CHAT_ID,
                #     'text': result_message,
                #     'parse_mode': 'HTML'  # Для поддержки форматирования (например, жирный текст)
                # }

                # telegram_response = requests.post(telegram_url, data=params)
                # if telegram_response.status_code == 200:
                #     print("Сообщение успешно отправлено в Telegram.")
                # else:
                #     print(f"Ошибка при отправке сообщения в Telegram: {telegram_response.text}")
        except json.JSONDecodeError:
            print("Ошибка: ответ не является JSON")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    else:
        print(f"Ошибка: {response.status_code}, ответ: {response.text}")


if __name__ == '__main__':
    fetch_and_send_transactions(input('Введите дату: '))
