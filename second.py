import json
import os

import requests

begin = '2024-10-30T00:00:00'  # формат даты: YYYY-MM-DDTHH:MM:SS
end = '2024-10-30T23:59:59'
base_url = 'https://lkapi.rn-card.ru/'  # Замените на ваш базовый URL сервера
result_type = 'JSON'
u = os.getenv('USERNAME')
p = os.getenv('PASSWORD')
contract = os.getenv('CONTRACT')


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
        with open("response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  # Сохранение в файл с отступами
        print("Данные сохранены в файл response.json")
    except json.JSONDecodeError:
        print("Ошибка: ответ не является JSON")
else:
    print(f"Ошибка: {response.status_code}, ответ: {response.text}")
