import io
import os
import textwrap
import time
import urllib.parse

import requests
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright


class TikTokSlideshowTool:
    """Інструмент для генерації та автоматичної публікації слайдів у TikTok."""

    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.session_id = None  # Сюди агент запише твій cookie

    def set_session_id(self, sessionid_cookie: str) -> str:
        """Зберігає cookie для того, щоб логінитись у TikTok без пароля."""
        self.session_id = sessionid_cookie
        return "Session ID успішно збережено в пам'яті агента. Я готовий до публікації!"

    def generate_slide(self, slide_number: int, prompt: str, text: str) -> str:
        """Генерує 1 слайд через Pollinations, накладає текст і зберігає локально."""
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))
            draw = ImageDraw.Draw(image)

            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except IOError:
                font = ImageFont.load_default()

            lines = textwrap.wrap(text, width=25)
            line_height = 70
            total_text_height = len(lines) * line_height
            start_y = 1000

            padding = 30
            draw.rectangle(
                [50, start_y - padding, 1030, start_y + total_text_height + padding],
                fill=(0, 0, 0, 180),
            )

            current_y = start_y
            for line in lines:
                draw.text((100, current_y), line, font=font, fill="white")
                current_y += line_height

            filename = f"slide_{slide_number}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)

            return f"УСПІХ: Слайд {slide_number} згенеровано."

        except Exception as e:
            return f"ПОМИЛКА при генерації слайду {slide_number}: {str(e)}"

    def publish_selected_slides(
        self, selected_slide_numbers: list, post_description: str
    ) -> str:
        """
        Відкриває безголовий браузер на VPS, логіниться через cookie,
        завантажує картинки та публікує карусель.
        """
        if not self.session_id:
            return "ПОМИЛКА: Ти ще не передав мені свій sessionid. Я не можу зайти в твій акаунт."

        files = [
            os.path.join(self.output_dir, f"slide_{num}.jpg")
            for num in selected_slide_numbers
        ]
        for f in files:
            if not os.path.exists(f):
                return f"ПОМИЛКА: Файл {f} не знайдено."

        try:
            with sync_playwright() as p:
                # Запускаємо браузер у фоновому режимі (headless=True для VPS)
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                # Підставляємо твою сесію (магія логіну)
                context.add_cookies(
                    [
                        {
                            "name": "sessionid",
                            "value": self.session_id,
                            "domain": ".tiktok.com",
                            "path": "/",
                        }
                    ]
                )

                page = context.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000)
                time.sleep(5)  # Чекаємо завантаження інтерфейсу

                # Завантажуємо всі картинки
                page.locator("input[type='file']").set_input_files(files)
                time.sleep(15)  # Даємо час ТікТоку обробити фотографії

                # Вводимо опис (Title + Hashtags)
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)

                # Натискаємо кнопку Post
                post_button = page.locator(
                    "button:has-text('Post'), button:has-text('Опублікувати')"
                ).first
                post_button.click()

                time.sleep(8)  # Чекаємо завершення публікації
                browser.close()

                return f"УСПІХ: Карусель з {len(files)} слайдів успішно опублікована в твоєму TikTok!"

        except Exception as e:
            return f"ПОМИЛКА при автоматичній публікації: {str(e)}"
