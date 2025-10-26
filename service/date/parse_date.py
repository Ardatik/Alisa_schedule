from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pymorphy3
from schemas.Alice_Request import Nlu
from dateutil.relativedelta import relativedelta

morph = pymorphy3.MorphAnalyzer()

weekday_dict = {
    1: "понедельник",
    2: "вторник", 
    3: "среда",
    4: "четверг",
    5: "пятница",
    6: "суббота",
    7: "воскресенье",
}

month_numbers = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}

def normalize_day_name(day):
    if not day:
        return day
    parsed = morph.parse(day.strip().lower())[0]
    lemma = parsed.normal_form
    valid_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    if lemma in valid_days:
        return lemma
    return day.strip().lower()

def parse_date(nlu: Nlu):
    entities = nlu.entities
    today = datetime.now(tz=ZoneInfo("Europe/Moscow")).date()
    tokens = [token.lower() for token in nlu.tokens]
    for token in tokens:
        if token == 'завтра':
            result_date = today + timedelta(days=1)
            print(f"[DEBUG] Распознано 'завтра': {result_date}")
            return result_date
        elif token == 'послезавтра':
            result_date = today + timedelta(days=2)
            print(f"[DEBUG] Распознано 'послезавтра': {result_date}")
            return result_date
        elif token == 'сегодня':
            print(f"[DEBUG] Распознано 'сегодня': {today}")
            return today
    for entity in entities:
        print(f"[DEBUG] Обрабатываем entity: {entity}")      
        if entity.type == 'YANDEX.DATETIME':
            value = entity.value
            print(f"[DEBUG] DATETIME value: {value}")
            if value.get('day_is_relative'):
                days_offset = value.get('day', 0)
                result_date = today + timedelta(days=days_offset)
                print(f"[DEBUG] Относительный день: смещение {days_offset}, дата: {result_date}")
                return result_date
            day = value.get('day')
            month = value.get('month')
            year = value.get('year', today.year)
            
            if day and month:
                try:
                    result_date = date(year, month, day)
                    print(f"[DEBUG] Абсолютная дата: {result_date}")
                    return result_date
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Ошибка создания даты: {e}")
                    continue
    for token in tokens:
        weekday = normalize_day_name(token)
        if weekday in weekday_dict.values():
            target_weekday_num = [k for k, v in weekday_dict.items() if v == weekday][0]
            current_weekday_num = today.isoweekday()
            
            days_ahead = target_weekday_num - current_weekday_num
            if days_ahead <= 0:
                days_ahead += 7
            result_date = today + timedelta(days=days_ahead)
            return result_date
    if len(tokens) >= 2:
        try:
            day_str = tokens[0]
            month_str = tokens[1]
            if day_str.isdigit() and month_str in month_numbers:
                day = int(day_str)
                month = month_numbers[month_str]
                year = today.year
                test_date = date(year, month, day)
                if test_date < today:
                    year += 1
                result_date = date(year, month, day)
                return result_date
        except (ValueError, KeyError) as e:
            print(f"Ошибка парсинга даты из токенов: {e}")
    return None