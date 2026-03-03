import os
import urllib.parse
import requests
import time
import random
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import io
from playwright.sync_api import sync_playwright

AVAILABLE_MODELS = {
    "flux": "Flux — дефолтна модель, якісні реалістичні зображення",
    "klein": "Klein — швидка та легка модель",
    "klein-large": "Klein Large — покращена версія Klein з більшою деталізацією",
    "gptimage": "GPT Image — модель від OpenAI, фотореалістичні зображення найвищої якості",
    "grok-imagine": "Grok Imagine — нова модель від xAI, креативні та яскраві зображення",
    "imagen-4": "Imagen 4 — модель від Google, чудова композиція та стилізація",
    "zimage": "Z-Image — швидка генерація з акцентом на чіткість",
}

class TikTokSlideshowTool:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.current_style_seed = random.randint(1, 9999999)
        self.state_file = os.path.join(self.output_dir, "tiktok_state.json")
        self.current_model = "flux"
        # Захист від безкінечного циклу
        self._consecutive_failures = 0
        self._last_failure_time = 0.0
        self._COOLDOWN_SECONDS = 120  # 2 хвилини кулдаун після серії помилок
        self._MAX_CONSECUTIVE_FAILURES = 3  # Після 3 помилок підряд — повний стоп
        self._stop_file = os.path.join(self.output_dir, "STOP")

    def _check_stop(self) -> bool:
        """Перевіряє чи користувач створив файл STOP для негайної зупинки."""
        if os.path.exists(self._stop_file):
            os.remove(self._stop_file)
            return True
        return False

    def list_models(self) -> str:
        result = "🎨 Доступні моделі для генерації:\n\n"
        for i, (model_id, desc) in enumerate(AVAILABLE_MODELS.items(), 1):
            active = " ✅" if model_id == self.current_model else ""
            result += f"{i}. {desc} (`{model_id}`){active}\n"
        result += "\nОбери номер або ID моделі."
        return result

    def set_model(self, model_id: str) -> str:
        model_id = model_id.lower().strip()
        if model_id not in AVAILABLE_MODELS:
            available = ", ".join(AVAILABLE_MODELS.keys())
            return f"ПОМИЛКА: Модель '{model_id}' не знайдена. Доступні: {available}"
        self.current_model = model_id
        self.current_style_seed = random.randint(1, 9999999)
        return f"Модель змінено на {AVAILABLE_MODELS[model_id]} (seed: {self.current_style_seed})"

    def _create_video_from_images(self, image_paths: list, output_filename="final_slideshow.mp4") -> str:
        video_path = os.path.join(self.output_dir, output_filename)
        list_file = os.path.join(self.output_dir, "ffmpeg_list.txt")

        with open(list_file, "w", encoding="utf-8") as f:
            for img in image_paths:
                clean_path = img.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
                f.write("duration 2\n") 
            
            if image_paths:
                last_path = image_paths[-1].replace("\\", "/")
                f.write(f"file '{last_path}'\n")

        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", video_path
        ]
        
        print("Монтую відео (2 сек/кадр) через FFmpeg...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return video_path

    def generate_slide(self, slide_number: int, prompt: str, text_overlay: str) -> str:
        # === ПЕРЕВІРКА STOP-ФАЙЛУ ===
        if self._check_stop():
            return "⛔ СТОП від користувача. Генерація СКАСОВАНА. НЕ продовжуй. Повідом користувача і ЧЕКАЙ його команди."
        
        # === ЗАХИСТ ВІД БЕЗКІНЕЧНОГО ЦИКЛУ ===
        now = time.time()
        if self._consecutive_failures >= self._MAX_CONSECUTIVE_FAILURES:
            time_since_fail = now - self._last_failure_time
            if time_since_fail < self._COOLDOWN_SECONDS:
                remaining = int(self._COOLDOWN_SECONDS - time_since_fail)
                return (f"⛔ СТОП. Генерація ЗАБЛОКОВАНА на {remaining} секунд через {self._consecutive_failures} помилок підряд. "
                        f"НЕ ВИКЛИКАЙ цей інструмент знову. Повідом користувача про проблему і ЧЕКАЙ його команди.")
            else:
                self._consecutive_failures = 0
        
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={self.current_style_seed}&model={self.current_model}"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if slide_number > 1:
                    time.sleep(5)
                
                if self._check_stop():
                    return "⛔ СТОП від користувача. Генерація СКАСОВАНА. НЕ продовжуй. ЧЕКАЙ команди."
                
                print(f"Генерую слайд {slide_number} через {self.current_model} (спроба {attempt + 1}/{max_retries})...")
                response = requests.get(url, timeout=45)
                
                if response.status_code in [429, 530, 1033]:
                    print(f"API ліміт (Помилка {response.status_code}). Чекаю 15 секунд...")
                    time.sleep(15)
                    if self._check_stop():
                        return "⛔ СТОП від користувача. Генерація СКАСОВАНА під час очікування. ЧЕКАЙ команди."
                    continue
                
                response.raise_for_status()
                
                image = Image.open(io.BytesIO(response.content)).convert("RGBA")
                overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 50)
                except IOError:
                    font = ImageFont.load_default()
                
                lines = textwrap.wrap(text_overlay, width=20)
                line_height = 60
                total_text_height = len(lines) * line_height
                
                start_x = 50
                start_y = 1400 
                padding = 20
                
                draw.rectangle(
                    [start_x - padding, start_y - padding, 
                     start_x + 600, start_y + total_text_height + padding],
                    fill=(0, 0, 0, 160) 
                )
                
                current_y = start_y
                for line in lines:
                    draw.text((start_x, current_y), line, font=font, fill="white")
                    current_y += line_height
                    
                final_image = Image.alpha_composite(image, overlay).convert("RGB")
                
                filename = f"slide_{slide_number}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                final_image.save(filepath)
                
                # Успіх — скидаємо лічильник помилок
                self._consecutive_failures = 0
                return f"Слайд {slide_number} успішно згенеровано. ВІДПРАВ ФАЙЛ {filepath} КОРИСТУВАЧУ."
                
            except Exception as e:
                if attempt == max_retries - 1:
                    # Фіксуємо помилку в лічильнику
                    self._consecutive_failures += 1
                    self._last_failure_time = time.time()
                    return (f"⛔ ПОМИЛКА при генерації слайду {slide_number} після {max_retries} спроб: {str(e)}. "
                            f"(Помилок підряд: {self._consecutive_failures}/{self._MAX_CONSECUTIVE_FAILURES}). "
                            f"НЕ ПРОБУЙ ЗНОВУ АВТОМАТИЧНО. Повідом користувача і ЧЕКАЙ його рішення.")
                
                print(f"Збій мережі: {e}. Чекаю 10 секунд перед повтором...")
                time.sleep(10)
                if self._check_stop():
                    return "⛔ СТОП від користувача. Генерація СКАСОВАНА. ЧЕКАЙ команди."

    def upload_video(self, selected_slide_numbers: list, post_description: str, action: str) -> str:
        if not os.path.exists(self.state_file):
            return "ПОМИЛКА: Файл tiktok_state.json не знайдено."

        image_files = [os.path.join(self.output_dir, f"slide_{num}.jpg") for num in selected_slide_numbers]
        for f in image_files:
            if not os.path.exists(f):
                return f"ПОМИЛКА: Файл {f} не знайдено."

        try:
            video_file = self._create_video_from_images(image_files)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    storage_state=self.state_file,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                
                page = context.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000)
                time.sleep(8) 
                
                if page.locator("input[type='file']").count() == 0:
                    browser.close()
                    return f"ПОМИЛКА ЛОГІНУ: Сесія злетіла."

                print("Завантажую змонтоване відео...")
                page.locator("input[type='file']").first.set_input_files(video_file)
                time.sleep(20) 
                
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                # 🔥 НОВЕ: Скролимо сторінку в самий низ, щоб кнопки збереження точно були в зоні видимості
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                if action.lower() == "publish":
                    # Використовуємо .last, бо головні кнопки завжди внизу сторінки
                    action_button = page.locator("button:has-text('Post'), button:has-text('Опублікувати')").last
                    action_button.click(force=True) # force=True пробиває будь-які перекриття
                    time.sleep(15)
                    status_msg = "ОПУБЛІКОВАНО В TIKTOK"
                else:
                    # Шукаємо кнопку чернетки (додали варіант 'Save' про всяк випадок)
                    action_button = page.locator("button:has-text('Save to draft'), button:has-text('Save'), button:has-text('Чернетка')").last
                    action_button.click(force=True)
                    time.sleep(15) # Збільшили час очікування, щоб ТікТок точно встиг зберегти
                    status_msg = "ЗБЕРЕЖЕНО В ЧЕРНЕТКИ (додай музику з телефону!)"
                
                success_path = os.path.join(self.output_dir, f"success_{action}.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: ВІДЕО {status_msg}! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ. Також ВІДПРАВ ФАЙЛ {video_file} КОРИСТУВАЧУ."
                
        except Exception as e:
            return f"КРИТИЧНА ПОМИЛКА: {str(e)}"