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

class TikTokSlideshowTool:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.current_style_seed = random.randint(1, 9999999)
        self.state_file = os.path.join(self.output_dir, "tiktok_state.json")

    def _create_video_from_images(self, image_paths: list, output_filename="final_slideshow.mp4") -> str:
        video_path = os.path.join(self.output_dir, output_filename)
        list_file = os.path.join(self.output_dir, "ffmpeg_list.txt")

        with open(list_file, "w", encoding="utf-8") as f:
            for img in image_paths:
                clean_path = img.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
                # 🔥 ЗМІНЕНО: 2 секунди на фото
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
        """Генерує картинку, накладає текст у куток і зберігає."""
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={self.current_style_seed}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Відкриваємо зображення для редагування
            image = Image.open(io.BytesIO(response.content)).convert("RGBA")
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            try:
                font = ImageFont.truetype("arial.ttf", 50)
            except IOError:
                font = ImageFont.load_default()
            
            # Розбиваємо текст на рядки (щоб не виліз за краї)
            lines = textwrap.wrap(text_overlay, width=20)
            line_height = 60
            total_text_height = len(lines) * line_height
            
            # Координати: лівий нижній кут (але вище інтерфейсу TikTok)
            start_x = 50
            start_y = 1400 
            padding = 20
            
            # Малюємо напівпрозору плашку для читабельності
            draw.rectangle(
                [start_x - padding, start_y - padding, 
                 start_x + 600, start_y + total_text_height + padding],
                fill=(0, 0, 0, 160) # Чорний з прозорістю
            )
            
            # Пишемо текст
            current_y = start_y
            for line in lines:
                draw.text((start_x, current_y), line, font=font, fill="white")
                current_y += line_height
                
            # Зводимо шари і зберігаємо
            final_image = Image.alpha_composite(image, overlay).convert("RGB")
            
            filename = f"slide_{slide_number}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            final_image.save(filepath)
            
            return f"Слайд {slide_number} успішно згенеровано з текстом '{text_overlay}'. ВІДПРАВ ФАЙЛ {filepath} КОРИСТУВАЧУ."
            
        except Exception as e:
            return f"ПОМИЛКА при генерації слайду {slide_number}: {str(e)}"

    def save_to_drafts(self, selected_slide_numbers: list, post_description: str) -> str:
        # Без змін, та сама логіка, що й в попередній версії
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

                page.locator("input[type='file']").first.set_input_files(video_file)
                time.sleep(20) 
                
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                draft_button = page.locator("button:has-text('Save to draft'), button:has-text('Зберегти в чернетки'), button:has-text('Чернетка')").first
                draft_button.click()
                time.sleep(10)
                
                success_path = os.path.join(self.output_dir, "success_draft.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: ВІДЕО збережено в Чернетки TikTok! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ. Також ВІДПРАВ ФАЙЛ {video_file} КОРИСТУВАЧУ."
                
        except Exception as e:
            return f"КРИТИЧНА ПОМИЛКА: {str(e)}"