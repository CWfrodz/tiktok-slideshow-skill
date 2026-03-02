import os
import urllib.parse
import requests
import time
import random
from playwright.sync_api import sync_playwright

class TikTokSlideshowTool:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.session_id = None
        self.current_style_seed = random.randint(1, 9999999)

    def set_session_id(self, sessionid_cookie: str) -> str:
        self.session_id = sessionid_cookie
        return "Session ID успішно збережено в пам'яті."

    def generate_slide(self, slide_number: int, prompt: str) -> str:
        """Генерує чисту картинку (без тексту) і зберігає локально."""
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={self.current_style_seed}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filename = f"slide_{slide_number}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"Слайд {slide_number} успішно згенеровано. Шлях до файлу: {filepath}. (Відправ цей файл користувачу для перевірки)"
            
        except Exception as e:
            return f"ПОМИЛКА при генерації слайду {slide_number}: {str(e)}"

    def save_to_drafts(self, selected_slide_numbers: list, post_description: str) -> str:
        """Завантажує картинки в TikTok, зберігає в чернетки та робить скріншот результату."""
        if not self.session_id:
            return "ПОМИЛКА: Немає sessionid. Запитай його у користувача."

        files = [os.path.join(self.output_dir, f"slide_{num}.jpg") for num in selected_slide_numbers]
        for f in files:
            if not os.path.exists(f):
                return f"ПОМИЛКА: Файл {f} не знайдено."

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                
                context.add_cookies([{
                    "name": "sessionid",
                    "value": self.session_id,
                    "domain": ".tiktok.com",
                    "path": "/"
                }])
                
                page = context.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000)
                time.sleep(8) 
                
                # Перевірка, чи ми взагалі зайшли в акаунт (чи є поле для файлів)
                if page.locator("input[type='file']").count() == 0:
                    debug_path = os.path.join(self.output_dir, "auth_error.png")
                    page.screenshot(path=debug_path)
                    browser.close()
                    return f"ПОМИЛКА ЛОГІНУ: TikTok не пустив нас на сторінку завантаження. Я зберіг скріншот екрана. ВІДПРАВ ФАЙЛ {debug_path} КОРИСТУВАЧУ В ТЕЛЕГРАМ, щоб він побачив причину."

                # Завантаження файлів
                page.locator("input[type='file']").set_input_files(files)
                time.sleep(15) 
                
                # Введення тексту та хештегів
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                # Натискання кнопки збереження в чернетки
                draft_button = page.locator("button:has-text('Save to draft'), button:has-text('Зберегти в чернетки'), button:has-text('Чернетка')").first
                draft_button.click()
                time.sleep(8)
                
                # Скріншот успішного збереження
                success_path = os.path.join(self.output_dir, "success_draft.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: Карусель збережена в Чернетки TikTok! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ В ТЕЛЕГРАМ як підтвердження успішної роботи."
                
        except Exception as e:
            # У разі будь-якої непередбачуваної помилки робимо скрін
            try:
                error_path = os.path.join(self.output_dir, "crash_error.png")
                page.screenshot(path=error_path)
                return f"КРИТИЧНА ПОМИЛКА Playwright: {str(e)}. ВІДПРАВ ФАЙЛ {error_path} КОРИСТУВАЧУ В ТЕЛЕГРАМ, щоб він побачив, на чому зламався браузер."
            except:
                return f"КРИТИЧНА ПОМИЛКА: {str(e)} (Не вдалося навіть зробити скріншот)."