---
name: tiktok-slideshow-skill
description: Generate AI image slideshows and publish them to TikTok. Use when user asks to create slideshow, TikTok video, or carousel content. Provides tools for image generation via Pollinations API with model selection, text overlay, video montage via FFmpeg, and automated TikTok upload.
---

# TikTok AI Video Publisher Skill

## 🤖 Інструкція для Агента

Ти маєш доступ до Python-класу `TikTokSlideshowTool` з файлу `tiktok_skill.py`.
Виконуй команди через `python3` або `exec_code`, НЕ через browser.

### Доступні інструменти (виклик через Python):

```python
from tiktok_skill import TikTokSlideshowTool
tool = TikTokSlideshowTool()

# 1. Показати доступні моделі генерації
result = tool.list_models()

# 2. Обрати модель
result = tool.set_model("flux")  # flux, klein, klein-large, gptimage, grok-imagine, imagen-4, zimage

# 3. Згенерувати слайд
result = tool.generate_slide(1, "English prompt for image", "Короткий текст")

# 4. Завантажити відео в TikTok
result = tool.upload_video([1,2,3,4,5], "Опис відео #хештеги", "draft")  # або "publish"
```

### ПРАВИЛО ПОМИЛОК (КРИТИЧНЕ)
Якщо інструмент повертає повідомлення з ⛔ або словом "ПОМИЛКА":
1. ЗУПИНИСЬ і НЕ викликай цей інструмент повторно автоматично.
2. Повідом користувача про помилку.
3. Запитай користувача що робити далі і ЧЕКАЙ його відповіді.
**НІКОЛИ не пробуй генерувати слайд повторно без прямої команди користувача.**

### АЛГОРИТМ РОБОТИ (СУВОРО ДОТРИМУЙСЯ):

* **Крок 0: Авторизація.** Якщо немає файлу `tiktok_state.json` в папці `tiktok_exports/`, попроси його у користувача.
* **Крок 1: Ідея.** Коли користувач пише "create slideshow", запитай тему. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 2: Заголовки.** Запропонуй 3-5 віральних тем. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 3: СТРУКТУРА ТА ТЕКСТ.** Покажи користувачу структуру кожного слайду:
  - Слайд N: Короткий текст (2-4 слова) + Ідея для фото
  Запитай: "Затверджуємо?". **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 4: Вибір моделі.** Виклич `tool.list_models()` і покажи список. Запитай яку модель використати. Після вибору виклич `tool.set_model(model_id)`. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 5: Вибір стилю.** Запропонуй 4 візуальні стилі. **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 6: Генерація слайдів.** Виклич `tool.generate_slide()` ДЛЯ КОЖНОГО слайду. Відправ користувачу згенеровані картинки.
* **Крок 7: Вибір дії.** Запитай: чернетка чи публікація? **ЧЕКАЙ ВІДПОВІДІ.**
* **Крок 8: Завантаження.** Згенеруй SEO-опис + хештеги. Виклич `tool.upload_video()`. Відправ результат.
