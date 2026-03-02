import os
import urllib.parse
import requests
import textwrap
import time
import random # ДОДАНО: для генерації seed
from PIL import Image, ImageDraw, ImageFont
import io
from playwright.sync_api import sync_playwright

class TikTokSlideshowTool:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "tiktok_exports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.session_id = None
        # ДОДАНО: Генеруємо унікальний сід для кожної нової сесії каруселі
        self.current_style_seed = random.randint(1, 9999999)

    def set_session_id(self, sessionid_cookie: str) -> str:
        self.session_id = sessionid_cookie
        return "Session ID успішно збережено."

    def generate_slide(self, slide_number: int, prompt: str, text: str) -> str:
        """Генерує 1 слайд. Використовує єдиний seed для збереження стилю."""
        encoded_prompt = urllib.parse.quote(prompt)
        
        # ДОДАНО: Параметр &seed=... для фіксації стилю
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={self.current_style_seed}"
        
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
                fill=(0, 0, 0, 180)
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
            
    # ... метод publish_selected_slides залишається без змін ...