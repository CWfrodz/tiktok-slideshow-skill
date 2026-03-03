import os
import time
import subprocess
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

class TikTokSlideshowTool:
    """Інструмент для обробки зображень, створення відео та публікації у TikTok."""
    
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.state_file = os.path.join(self.output_dir, "tiktok_state.json")

    def _add_text_to_images(self, image_paths: list, overlay_texts: list) -> list:
        processed_paths = []
        for i, (img_path, raw_text) in enumerate(zip(image_paths, overlay_texts)):
            if not os.path.exists(img_path):
                continue
            try:
                clean_text = re.sub(r'[^a-zA-Zа-яА-ЯіІїЇєЄґҐ0-9\s.,!?\'"()\-+%$€]', '', raw_text)
                
                image = Image.open(img_path).convert("RGBA")
                overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 55)
                except IOError:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 55)
                    except IOError:
                        font = ImageFont.load_default()
                
                lines = textwrap.wrap(clean_text, width=25)
                
                bbox_test = draw.textbbox((0, 0), "Ag", font=font)
                line_height = bbox_test[3] - bbox_test[1] + 35
                    
                total_text_height = len(lines) * line_height
                
                max_line_width = 0
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    lw = bbox[2] - bbox[0]
                    if lw > max_line_width:
                        max_line_width = lw
                
                image_width = 1080
                start_y = 1200 
                padding_x = 40
                padding_y = 30
                
                box_x1 = max(0, (image_width - max_line_width) // 2 - padding_x)
                box_x2 = min(image_width, (image_width + max_line_width) // 2 + padding_x)
                box_y1 = start_y - padding_y
                box_y2 = start_y + total_text_height + padding_y
                
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 180))
                
                current_y = start_y
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    lw = bbox[2] - bbox[0]
                    line_x = (image_width - lw) // 2
                    draw.text((line_x, current_y), line, font=font, fill="white")
                    current_y += line_height
                    
                final_image = Image.alpha_composite(image, overlay).convert("RGB")
                
                filename = f"processed_slide_{i}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                final_image.save(filepath)
                processed_paths.append(filepath)
            except Exception as e:
                print(f"Помилка обробки тексту для {img_path}: {e}")
                processed_paths.append(img_path) 
                
        return processed_paths

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
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return video_path

    # 🔥 ОНОВЛЕНО: Додано параметр song_name
    def upload_video(self, image_paths: list, overlay_texts: list, post_description: str, action: str, song_name: str = "") -> str:
        """Обробляє фото, монтує відео, ДОДАЄ МУЗИКУ та завантажує в TikTok."""
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
                
                # 🔥 НОВЕ: Логіка пошуку та додавання музики 🔥
                if song_name and song_name.lower() not in ["none", "немає", "без музики", "ні"]:
                    try:
                        print(f"Шукаю музику: {song_name}...")
                        # Натискаємо кнопку Sounds
                        sounds_btn = page.locator("text='Sounds', text='Звуки', div:has-text('Sounds')").locator("visible=true").first
                        sounds_btn.click(timeout=10000)
                        time.sleep(3)
                        
                        # Вводимо назву пісні у пошук
                        search_input = page.locator("input[placeholder*='Search'], input[type='search'], input[type='text']").last
                        search_input.fill(song_name)
                        search_input.press("Enter")
                        time.sleep(6) # Чекаємо, поки ТікТок знайде треки
                        
                        # Натискаємо кнопку Use (Використати) на першому результаті
                        use_btn = page.locator("button:has-text('Use'), button:has-text('Використати')").first
                        use_btn.click(timeout=10000)
                        print("Музику успішно застосовано!")
                        time.sleep(3)
                    except Exception as music_err:
                        print(f"УВАГА: Не вдалося додати музику '{song_name}', продовжую без неї. Помилка: {music_err}")
                
                # Введення опису
                editor = page.locator(".public-DraftEditor-content")
                editor.click()
                editor.fill(post_description)
                
                print("Чекаю 15 секунд на фонові перевірки TikTok...")
                time.sleep(15)
                
                try:
                    post_btn = page.locator("button", has_text=re.compile(r"Post|Опублікувати")).last
                    post_btn.scroll_into_view_if_needed()
                    time.sleep(2) 
                    
                    post_btn.click(force=True)
                        
                    print("Натиснуто POST. Чекаю 25 секунд для завершення публікації...")
                    time.sleep(25) 
                    status_msg = "ОПУБЛІКОВАНО В TIKTOK"
                except Exception as e:
                    print(f"Помилка натискання кнопки POST: {e}")
                    status_msg = "ПОМИЛКА КЛІКУ ПО КНОПЦІ"

                success_path = os.path.join(self.output_dir, f"success_publish.png")
                page.screenshot(path=success_path)
                browser.close()
                
                return f"УСПІХ: ВІДЕО {status_msg}! ВІДПРАВ ФАЙЛ {success_path} КОРИСТУВАЧУ В ТЕЛЕГРАМ ЧАТ. Також ВІДПРАВ ФАЙЛ {video_file} КОРИСТУВАЧУ В ТЕЛЕГРАМ ЧАТ."
                
        except Exception as e:
            return f"КРИТИЧНА ПОМИЛКА: {str(e)}"