#!/usr/bin/env python3
"""CLI обгортка для TikTokSlideshowTool.
Використання:
  python3 run.py list_models
  python3 run.py set_model flux
  python3 run.py generate <номер> <промпт> <текст>
  python3 run.py upload <номери через кому> <опис> <draft|publish>
"""
import sys
import os

# Додаємо поточну директорію скіла в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiktok_skill import TikTokSlideshowTool

tool = TikTokSlideshowTool()

def main():
    if len(sys.argv) < 2:
        print("Використання: python3 run.py <команда> [аргументи]")
        print("Команди: list_models, set_model, generate, upload")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list_models":
        print(tool.list_models())
    
    elif cmd == "set_model":
        if len(sys.argv) < 3:
            print("ПОМИЛКА: вкажи ID моделі. Приклад: python3 run.py set_model flux")
            sys.exit(1)
        print(tool.set_model(sys.argv[2]))
    
    elif cmd == "generate":
        if len(sys.argv) < 5:
            print("ПОМИЛКА: python3 run.py generate <номер_слайду> <промпт_англійською> <текст_на_слайді>")
            sys.exit(1)
        slide_num = int(sys.argv[2])
        prompt = sys.argv[3]
        text_overlay = sys.argv[4]
        print(tool.generate_slide(slide_num, prompt, text_overlay))
    
    elif cmd == "upload":
        if len(sys.argv) < 5:
            print("ПОМИЛКА: python3 run.py upload <номери: 1,2,3> <опис_відео> <draft|publish>")
            sys.exit(1)
        numbers = [int(n) for n in sys.argv[2].split(",")]
        description = sys.argv[3]
        action = sys.argv[4]
        print(tool.upload_video(numbers, description, action))
    
    else:
        print(f"ПОМИЛКА: Невідома команда '{cmd}'. Доступні: list_models, set_model, generate, upload")
        sys.exit(1)

if __name__ == "__main__":
    main()
