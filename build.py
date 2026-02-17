import requests
import json

# НАСТРОЙКИ
GROUP_NAME = "ПКБО-01-24"
API_URL = f"https://schedule-of.mirea.ru/schedule/api/search?match={GROUP_NAME}"

# Сопоставление типов пар с нашими CSS классами
TYPE_MAP = {
    "Лек": ("type-lk", "Лекция"),
    "Прак": ("type-pr", "Практика"),
    "Лаб": ("type-lab", "Лаб")
}

# Дни недели (в API они идут 1-6)
DAYS_MAP = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота"}

# Время пар
TIME_MAP = {
    1: ("09:00", "10:30"),
    2: ("10:40", "12:10"),
    3: ("12:40", "14:10"),
    4: ("14:20", "15:50"),
    5: ("16:20", "17:50"),
    6: ("18:00", "19:30"),
    7: ("19:40", "21:10") # На всякий случай
}

def get_schedule_data():
    print(f"🔍 Поиск группы {GROUP_NAME}...")
    try:
        # 1. Получаем расписание через API сообщества (парсит официальный сайт)
        response = requests.get(API_URL)
        data = response.json()
        
        if len(data['data']) == 0:
            print("❌ Группа не найдена!")
            return None
            
        return data['data'][0] # Возвращаем объект группы с расписанием
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return None

def generate_week_html(schedule_data, week_num):
    # week_num: 1-4
    # Логика четности для МИРЭА: 
    # Недели 1, 3 - нечетные (odd)
    # Недели 2, 4 - четные (even)
    parity = 1 if (week_num % 2 != 0) else 2 
    
    html = f'''
    <!-- === НЕДЕЛЯ {week_num} === -->
    <div id="week-{week_num}" class="week-content">
        <div class="week-visual-header">
            <div class="big-label">Учебная неделя</div>
            <div class="big-num">0{week_num}</div>
        </div>
        <div class="days-wrapper">
    '''
    
    # Итерируемся по дням недели (1..6)
    # В структуре API schedule-of.mirea: schedule[day_iso][lesson_num]
    # Но формат может отличаться, используем упрощенный проход
    
    # Примечание: API возвращает сложную структуру. Упростим разбор.
    # Обычно там структура: data['schedule'] -> словарь дней
    
    schedule = schedule_data.get('schedule', {})
    
    has_lessons_in_week = False

    for day_num in range(1, 7): # Понедельник - Суббота
        day_str = str(day_num)
        if day_str not in schedule:
            continue
            
        day_lessons = schedule[day_str]
        
        # Собираем HTML для одного дня
        day_html = ""
        has_day_content = False
        
        # Сортируем пары по номеру
        for pair_num in sorted(day_lessons.keys(), key=int):
            lessons = day_lessons[pair_num] # Это список (может быть несколько пар в одно время для разных подгрупп/недель)
            
            for lesson in lessons:
                # Фильтр по неделям (lesson['weeks'] - список недель, когда пара есть)
                if week_num not in lesson['weeks']:
                    continue
                
                # Данные пары
                subject = lesson['name']
                t_type = lesson['type']
                teacher = lesson['teacher'] if lesson['teacher'] else "Кафедра"
                class_room = lesson['classrooms'][0] if lesson['classrooms'] else ""
                
                # Определение CSS класса
                css_class, badge_text = TYPE_MAP.get(t_type, ("type-pr", t_type))
                
                # Временные метки
                time_start, time_end = TIME_MAP.get(int(pair_num), ("00:00", "00:00"))
                
                # Доп. инфо (аудитория)
                details = teacher
                if class_room:
                    details += f" • {class_room}"

                # Генерация HTML одной пары
                pair_html = f'''
                <div class="pair-item {css_class}">
                    <div class="pair-time"><div class="num">{pair_num}</div><div class="interval"><span>{time_start}</span><span>{time_end}</span></div></div>
                    <div class="pair-content">
                        <div class="subject">{subject}</div>
                        <div class="teacher">{details}</div>
                        <span class="badge">{badge_text}</span>
                    </div>
                </div>
                '''
                day_html += pair_html
                has_day_content = True
        
        if has_day_content:
            has_lessons_in_week = True
            html += f'''
            <div class="day-card">
                <div class="day-header">{DAYS_MAP[day_num]}</div>
                {day_html}
            </div>
            '''
            
    if not has_lessons_in_week:
        html += '<div style="text-align:center; padding: 2rem; color: #999;">Занятий нет</div>'

    html += '''
        </div>
    </div>
    '''
    return html

def main():
    # 1. Читаем шаблон
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print("❌ Ошибка: Файл template.html не найден!")
        return

    # 2. Получаем данные
    data = get_schedule_data()
    if not data:
        return

    # 3. Генерируем HTML для 4 недель
    full_schedule_html = ""
    for w in range(1, 5):
        print(f"⚙️ Генерация недели {w}...")
        full_schedule_html += generate_week_html(data, w)

    # 4. Собираем итоговый файл
    final_html = template.replace("{{SCHEDULE_CONTENT}}", full_schedule_html)
    
    # 5. Сохраняем
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print("✅ Готово! Файл index.html создан и синхронизирован.")

if __name__ == "__main__":
    main()
