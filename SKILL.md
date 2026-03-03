---
name: tiktok-slideshow-skill
description: Generate AI image slideshows and publish them to TikTok. Use when user asks to create slideshow, TikTok video, or carousel content. Run commands via python3 run.py in the skill directory.
---

# TikTok AI Video Publisher Skill

## ⚠️ ГОЛОВНЕ ПРАВИЛО

**ВСІ операції виконуй ТІЛЬКИ через `python3 run.py` в директорії скіла.**
**НЕ пиши свій код. НЕ генеруй зображення через curl, wget, чи browser.**
**НЕ запускай browser/playwright subagent для генерації картинок.**

Директорія скіла:
```
cd /root/.openclaw/workspace/skills/tiktok-slideshow-skill/
```

## 🛠 Доступні команди

```bash
# Показати доступні моделі генерації
python3 run.py list_models

# Обрати модель
python3 run.py set_model flux

# Згенерувати слайд (номер, промпт англійською, текст на слайді)
python3 run.py generate 1 "epic sunset over mountains, cinematic" "Вечірні гори"

# Завантажити відео в TikTok
python3 run.py upload "1,2,3,4,5" "Опис відео #хештеги" "draft"
```

## 🚨 ПРАВИЛО ПОМИЛОК

Якщо команда повертає ⛔ або "ПОМИЛКА":
1. ЗУПИНИСЬ.
2. Повідом користувача.
3. ЧЕКАЙ його команди.
**НІКОЛИ не повторюй автоматично.**

## 📋 АЛГОРИТМ (СУВОРО ДОТРИМУЙСЯ)

### Крок 0: Авторизація
Для публікації в TikTok потрібен файл `tiktok_state.json` (НЕ sessionid cookie, а ПОВНИЙ JSON файл стану Playwright браузерної сесії).
Перевір: `ls tiktok_exports/tiktok_state.json`.
Якщо файлу немає — скажи користувачу:
> "Для публікації мені потрібен файл tiktok_state.json (Playwright storage state). Надішли його, і я збережу в tiktok_exports/."

**НЕ ПИТАЙ sessionid cookie. Потрібен саме файл tiktok_state.json.**

### Крок 1: Ідея
Коли користувач пише "create slideshow" — запитай тему. **ЧЕКАЙ ВІДПОВІДІ.**

### Крок 2: Заголовки
Запропонуй 3-5 віральних тем. **ЧЕКАЙ ВІДПОВІДІ.**

### Крок 3: Структура та текст
Покажи структуру кожного слайду:
- Слайд N: Короткий текст (2-4 слова) + Ідея для генерації фото
Запитай: "Затверджуємо?". **ЧЕКАЙ ВІДПОВІДІ.**

### Крок 4: Вибір моделі
Виконай: `python3 run.py list_models`
Покажи список користувачу. **ЧЕКАЙ ВІДПОВІДІ.**
Після вибору: `python3 run.py set_model <id>`

### Крок 5: Вибір стилю
Запропонуй 4 візуальні стилі. **ЧЕКАЙ ВІДПОВІДІ.**

### Крок 6: Генерація слайдів
Виконай `python3 run.py generate` для КОЖНОГО слайду окремо.
Відправ згенеровані картинки користувачу (шлях буде в результаті).

### Крок 7: Вибір дії
Запитай: чернетка чи публікація? **ЧЕКАЙ ВІДПОВІДІ.**

### Крок 8: Завантаження
Згенеруй SEO-опис + 6-8 хештегів.
Виконай: `python3 run.py upload "1,2,3,4,5" "опис #хештеги" "draft"`
