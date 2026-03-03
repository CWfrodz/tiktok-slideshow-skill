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
        """Накладає адаптивний відцентрований текст на картинки."""
        processed_paths = []
        for i, (img_path, raw_text) in enumerate(zip(image_paths, overlay_texts)):
            if not os.path.exists(img_path):
                continue
            try:
                # Очищаємо текст від емодзі та складних символів (залишаємо кирилицю, латиницю, базову пунктуацію)
                text = ''.join(c for c in raw_text if ord(c) < 0x2600)
                
                image = Image.open(img_path).convert("RGBA")
                overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 55)
                except IOError:
                    font = ImageFont.load_default()
                
                # Розбиваємо текст на рядки (максимум 25 символів у рядку, щоб точно влізло в ширину екрана)
                lines = textwrap.wrap(text, width=25)
                
                # Універсальне визначення висоти рядка для різних версій Pillow
                if hasattr(draw, 'textbbox'):
                    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + 15
                else:
                    line_height = draw.textsize("Ag", font=font)[1] + 15
                    
                total_text_height = len(lines) * line_height
                
                # Знаходимо найширший рядок, щоб підігнати під нього чорну плашку
                max_line_width = 0
                for line in lines:
                    if hasattr(draw, 'textbbox'):
                        lw = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
                    else:
                        lw = draw.textsize(line, font=font)[0]
                    if lw > max_line_width:
                        max_line_width = lw
                
                image_width = 1080
                start_y = 1200 # Висота розміщення (щоб не перекривало опис відео в ТікТоці)
                padding_x = 40
                padding_y = 30
                
                # Координати адаптивної чорної плашки по центру
                box_x1 = max(0, (image_width - max_line_width) // 2 - padding_x)
                box_x2 = min(image_width, (image_width + max_line_width) // 2 + padding_x)
                box_y1 = start_y - padding_y
                box_y2 = start_y + total_text_height + padding_y
                
                # Малюємо плашку
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 180))
                
                # Пишемо ідеально відцентрований текст
                current_y = start_y
                for line in lines:
                    if hasattr(draw, 'textbbox'):
                        lw = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
                    else:
                        lw = draw.textsize(line, font=font)[0]
                        
                    line_x = (image_width - lw) // 2
                    draw.text((line_x, current_y), line, font=font, fill="white")
                    current_y += line_height
                    
                final_image = Image.alpha_composite(image, overlay).convert("RGB")
                
                filename = f"processed_slide_{i}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                final_image.save(filepath)
                processed_paths.append(filepath)
            except Exception as e:
                print(f"Помилка обробки {img_path}: {e}")
                processed_paths.append(img_path) 
                
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
            processed_images = self._add_text_to_images(image_paths, overlay_texts)
            video_file = self._create_video_from_images(processed_images)

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
                
                try:
                    accept_button = page.locator("button:has-text('Allow all')").first
                    if accept_button.is_visible():
                        accept_button.click()
                        time.sleep(2)
                except:
                    pass
                
                if page.locator("input[type='file']").count() == 0:
                    browser.close()
                    return f"ПОМИЛКА ЛОГІНУ: Сесія злетіла."

                print("Завантажую змонтоване відео...")
                page.locator("input[type='file']").first.set_input_files(video_file)
                time.sleep(25) 
                
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                time.sleep(2)
                
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                if action.lower() == "publish":
                    action_button = page.locator("button:has-text('Post'), button:has-text('Опублікувати')").last
                    action_button.click(force=True)
                    time.sleep(25) 
                    status_msg = "ОПУБЛІКОВАНО В TIKTOK"
                else:
                    action_button = page.locator("button:has-text('Save to draft'), button:has-text('Save'), button:has-text('Чернетка')").last
                    action_button.click(force=True)
                    time.sleep(20) 
                    status_msg = "ЗБЕРЕЖЕНО В ЧЕРНЕТКИ (додай музику з телефону!)"
                
                success_path = os.path.join(self.output_dir, f"success_{action}.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: ВІДЕО {status_msg}! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ. Також ВІДПРАВ ФАЙЛ {video_file} КОРИСТУВАЧУ."
                
        except Exception as e:
            return f"КРИТИЧНА ПОМИЛКА: {str(e)}"