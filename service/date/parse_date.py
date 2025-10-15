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
    tokens = nlu.tokens
    
    for entity in entities:
        print('\n','entity: ',entity)
        if entity.type == 'YANDEX.DATETIME':
            value = entity.value
            print('\n','value: ','\t',value)
            day = value.get('day', None)
            month = value.get('month', None)
            year = value.get('year', None)
            if year is None:
                year = today.year
            print('\n','day: ','\t',day,)
            print('\n','month: ','\t',month)
            print('\n','year: ','\t',year)
            
            schedule_date = None
            
            if value.get('day_is_relative') == False and value.get('month_is_relative') == False:
                try:
                    schedule_date = date(year, month, day)
                except (ValueError, TypeError):
                    return None
            elif value.get('day_is_relative') == True and value.get('month_is_relative') == False:
                schedule_date = today + relativedelta(days=value.get("day", 0))
            elif value.get('day_is_relative') == True and value.get('month_is_relative') == True:
                schedule_date = today + relativedelta(months=month, days=day)
            else:
                schedule_date = today
            
            if schedule_date:
                return schedule_date
    
    for token in tokens:
        weekday = normalize_day_name(token)
        weekday_iso = None
        for key, value in weekday_dict.items():
            if value == weekday:
                weekday_iso = key
                break  
        if weekday_iso is not None:
            days_ahead = weekday_iso - today.isoweekday()
            if days_ahead < 0:
                days_ahead += 7  
            return today + timedelta(days=days_ahead)
    
    return None