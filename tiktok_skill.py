import os
import time
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

class TikTokSlideshowTool:
    """Інструмент для обробки зображень, створення відео та публікації у TikTok."""
    
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.state_file = os.path.join(self.output_dir, "tiktok_state.json")

    def _add_text_to_images(self, image_paths: list, overlay_texts: list) -> list:
        """Накладає текст на картинки, які згенерував агент."""
        processed_paths = []
        for i, (img_path, text) in enumerate(zip(image_paths, overlay_texts)):
            if not os.path.exists(img_path):
                continue
            try:
                image = Image.open(img_path).convert("RGBA")
                overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 50)
                except IOError:
                    font = ImageFont.load_default()
                
                lines = textwrap.wrap(text, width=20)
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
                
                filename = f"processed_slide_{i}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                final_image.save(filepath)
                processed_paths.append(filepath)
            except Exception as e:
                print(f"Помилка обробки {img_path}: {e}")
                processed_paths.append(img_path) # У разі помилки беремо оригінал
                
        return processed_paths

    def _create_video_from_images(self, image_paths: list, output_filename="final_slideshow.mp4") -> str:
        """Зшиває картинки у відео (2 сек/кадр) через FFmpeg."""
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
        
        print("Монтую відео через FFmpeg...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return video_path

    def upload_video(self, image_paths: list, overlay_texts: list, post_description: str, action: str) -> str:
        """Обробляє фото, монтує відео та завантажує в TikTok (Чернетка/Публікація)."""
        if not os.path.exists(self.state_file):
            return "ПОМИЛКА: Файл tiktok_state.json не знайдено."

        try:
            # 1. Накладаємо текст і монтуємо відео
            processed_images = self._add_text_to_images(image_paths, overlay_texts)
            video_file = self._create_video_from_images(processed_images)

            # 2. Відкриваємо браузер
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
                
                # 🔥 НОВЕ: Приймаємо кукі (Allow All), якщо плашка з'явилася
                try:
                    accept_button = page.locator("button:has-text('Allow all')").first
                    if accept_button.is_visible():
                        accept_button.click()
                        time.sleep(2)
                        print("Кукі успішно прийнято.")
                except:
                    pass
                
                if page.locator("input[type='file']").count() == 0:
                    browser.close()
                    return f"ПОМИЛКА ЛОГІНУ: Сесія злетіла."

                print("Завантажую змонтоване відео...")
                page.locator("input[type='file']").first.set_input_files(video_file)
                time.sleep(25) # Чекаємо, поки відео обробиться сервером ТікТоку
                
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                # Скролимо в самий низ
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Вибір дії: Публікація чи Чернетка
                if action.lower() == "publish":
                    # Шукаємо кнопку Post
                    action_button = page.locator("button:has-text('Post'), button:has-text('Опублікувати')").last
                    action_button.click(force=True)
                    print("Натиснуто POST. Чекаю 25 секунд для завершення публікації...")
                    # 🔥 НОВЕ: Залізобетонна пауза, щоб ТікТок встиг обробити клік і зберегти відео
                    time.sleep(25) 
                    status_msg = "ОПУБЛІКОВАНО В TIKTOK"
                else:
                    # Шукаємо кнопку Draft
                    action_button = page.locator("button:has-text('Save to draft'), button:has-text('Save'), button:has-text('Чернетка')").last
                    action_button.click(force=True)
                    print("Натиснуто Зберегти в чернетки. Чекаю 20 секунд...")
                    time.sleep(20) 
                    status_msg = "ЗБЕРЕЖЕНО В ЧЕРНЕТКИ (додай музику з телефону!)"
                
                success_path = os.path.join(self.output_dir, f"success_{action}.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: ВІДЕО {status_msg}! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ. Також ВІДПРАВ ФАЙЛ {video_file} КОРИСТУВАЧУ."
                
        except Exception as e:
            return f"КРИТИЧНА ПОМИЛКА: {str(e)}"