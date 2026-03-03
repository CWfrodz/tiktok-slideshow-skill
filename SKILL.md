---
name: tiktok-slideshow-skill
description: Generate AI image slideshows and publish them to TikTok. Use when user asks to create slideshow, TikTok video, or carousel content. Run commands via python3 run.py in the skill directory.
---

# TikTok AI Video Publisher Skill

## 🛠 Як виконувати команди

**ВАЖЛИВО:** Всі команди виконуй через `python3 run.py` в директорії скіла.
**НЕ використовуй browser/playwright subagent для генерації!**
Playwright використовується тільки всередині `upload` для завантаження в TikTok.

Директорія скіла: `/root/.openclaw/workspace/skills/tiktok-slideshow-skill/`

### Доступні команди:

```bash
cd /root/.openclaw/workspace/skills/tiktok-slideshow-skill/

# 1. Показати доступні моделі генерації
python3 run.py list_models

# 2. Обрати модель
python3 run.py set_model flux
# Доступні: flux, klein, klein-large, gptimage, grok-imagine, imagen-4, zimage

# 3. Згенерувати слайд (номер, промпт англійською, текст на слайді)
python3 run.py generate 1 "epic sunset over mountains, cinematic style" "Вечірні гори"

# 4. Завантажити відео в TikTok (номери слайдів, опис, draft або publish)
python3 run.py upload "1,2,3,4,5" "Мій крутий контент #тікток #viral" "draft"
```

### ПРАВИЛО ПОМИЛОК (КРИТИЧНЕ)
Якщо команда повертає повідомлення з ⛔ або словом "ПОМИЛКА":
1. **ЗУПИНИСЬ** і НЕ повторюй команду автоматично.
2. Повідом користувача про помилку.
3. **ЧЕКАЙ** його відповіді.
**НІКОЛИ не пробуй генерувати слайд повторно без прямої команди користувача.**

### АЛГОРИТМ РОБОТИ (СУВОРО ДОТРИМУЙСЯ, НЕ ПРОПУСКАЙ КРОКИ):

* **Крок 0: Авторизація.** Перевір чи є файл `tiktok_exports/tiktok_state.json`. Якщо ні — попроси у користувача.
* **Крок 1: Ідея.** Коли користувач пише "create slideshow", запитай тему. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 2: Заголовки.** Запропонуй 3-5 віральних тем. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 3: СТРУКТУРА ТА ТЕКСТ.** Покажи користувачу структуру кожного слайду. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 4: Вибір моделі.** Виконай `python3 run.py list_models` і покажи список. **ЧЕКАЙ ВІДПОВІДІ.** Після вибору: `python3 run.py set_model <id>`.
* **Крок 5: Вибір стилю.** Запропонуй 4 візуальні стилі. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 6: Генерація слайдів.** Виконай `python3 run.py generate` для КОЖНОГО слайду. Відправ картинки користувачу.
* **Крок 7: Вибір дії.** Чернетка чи публікація? **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 8: Завантаження.** Згенеруй SEO-опис + хештеги. Виконай `python3 run.py upload`.
