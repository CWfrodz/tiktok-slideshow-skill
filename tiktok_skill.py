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
        self.current_style_seed = random.randint(1, 9999999)
        # Файл, де Playwright зберігатиме всю сесію (включаючи кукі і LocalStorage)
        self.state_file = os.path.join(self.output_dir, "tiktok_state.json")

    def login_via_qr(self) -> str:
        """
        Відкриває сторінку логіну, натискає на QR-код, робить скріншот і чекає на сканування.
        Після успіху зберігає стан сесії.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()
                page.goto("https://www.tiktok.com/login", timeout=60000)
                time.sleep(5)

                # Закриваємо плашку "Allow cookies", якщо вона є
                try:
                    decline_button = page.locator("button:has-text('Decline optional cookies')").first
                    if decline_button.is_visible():
                        decline_button.click()
                        time.sleep(1)
                except:
                    pass

                # Натискаємо "Use QR code" (шукаємо лінк або кнопку з таким текстом)
                qr_button = page.locator("text='Use QR code'").first
                if not qr_button.is_visible():
                    # Якщо щось не так з інтерфейсом, робимо дебаг-скріншот
                    debug_path = os.path.join(self.output_dir, "qr_error.png")
                    page.screenshot(path=debug_path)
                    return f"ПОМИЛКА: Не знайшов кнопку QR-коду. ВІДПРАВ ФАЙЛ {debug_path} КОРИСТУВАЧУ."

                qr_button.click()
                time.sleep(5) # Чекаємо, поки QR-код згенерується

                # Робимо скріншот QR-коду
                qr_path = os.path.join(self.output_dir, "scan_me.png")
                page.screenshot(path=qr_path)
                
                # ЦЕ ВАЖЛИВО: Ми повертаємо шлях до картинки агенту, але ПОВИННІ почекати, 
                # поки користувач відсканує. Тому ми робимо паузу прямо в коді.
                print("Чекаю на сканування QR-коду (60 секунд)...")
                
                # Чекаємо 60 секунд. Якщо ти відскануєш, сторінка сама перезавантажиться.
                page.wait_for_timeout(60000) 
                
                # Зберігаємо стан сесії (всі кукі, токени) у файл
                context.storage_state(path=self.state_file)
                browser.close()

                return f"АВТОРИЗАЦІЯ ЗАВЕРШЕНА. ВІДПРАВ ФАЙЛ {qr_path} КОРИСТУВАЧУ, щоб він бачив, який QR-код було відкрито. Якщо користувач встиг відсканувати за 60 секунд, сесія збережена у файл."
                
        except Exception as e:
            return f"ПОМИЛКА при генерації QR-коду: {str(e)}"


    def generate_slide(self, slide_number: int, prompt: str) -> str:
        # Без змін
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={self.current_style_seed}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            filename = f"slide_{slide_number}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"Слайд {slide_number} успішно згенеровано. ВІДПРАВ ФАЙЛ {filepath} КОРИСТУВАЧУ."
        except Exception as e:
            return f"ПОМИЛКА при генерації слайду {slide_number}: {str(e)}"

    def save_to_drafts(self, selected_slide_numbers: list, post_description: str) -> str:
        """Завантажує картинки, використовуючи збережений стан сесії."""
        if not os.path.exists(self.state_file):
            return "ПОМИЛКА: Файл tiktok_state.json не знайдено. Спочатку потрібно викликати login_via_qr."

        files = [os.path.join(self.output_dir, f"slide_{num}.jpg") for num in selected_slide_numbers]
        for f in files:
            if not os.path.exists(f):
                return f"ПОМИЛКА: Файл {f} не знайдено."

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                # СТВОРЮЄМО КОНТЕКСТ ЗІ ЗБЕРЕЖЕНОГО СТАНУ (Включає логін)
                context = browser.new_context(
                    storage_state=self.state_file,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                
                page = context.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000)
                time.sleep(8) 
                
                if page.locator("input[type='file']").count() == 0:
                    debug_path = os.path.join(self.output_dir, "auth_error.png")
                    page.screenshot(path=debug_path)
                    browser.close()
                    return f"ПОМИЛКА ЛОГІНУ: Сесія злетіла. ВІДПРАВ ФАЙЛ {debug_path} КОРИСТУВАЧУ і запропонуй перелогінитись."

                page.locator("input[type='file']").set_input_files(files)
                time.sleep(15) 
                
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                draft_button = page.locator("button:has-text('Save to draft'), button:has-text('Зберегти в чернетки'), button:has-text('Чернетка')").first
                draft_button.click()
                time.sleep(8)
                
                success_path = os.path.join(self.output_dir, "success_draft.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: Карусель збережена в Чернетки TikTok! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ."
                
        except Exception as e:
            try:
                error_path = os.path.join(self.output_dir, "crash_error.png")
                page.screenshot(path=error_path)
                return f"КРИТИЧНА ПОМИЛКА: {str(e)}. ВІДПРАВ ФАЙЛ {error_path} КОРИСТУВАЧУ."
            except:
                return f"КРИТИЧНА ПОМИЛКА: {str(e)}"