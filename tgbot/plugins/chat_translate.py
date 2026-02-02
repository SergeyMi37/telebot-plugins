# Функции для перевода текста с помощью Ollama
# --------- ISO 639-1 - код языка
# Китайский	Chinese	zh
# Английский	English	en
# Арабский	Arabic	ar
# Хинди	Hindi	hi
# Испанский	Spanish	es
# Французский	French	fr
# Русский	Russian	ru
# Португальский	Portuguese	pt
# Бенгальский	Bengali	bn
# Немецкий	German	de
# Японский	Japanese	ja
# ----- Хорошо работают и без GPU
# 1 --model "lauchacarro/qwen2.5-translator:latest" 
# 2 --model "icky/translate:latest" 
# 3 --model "SimonPu/Hunyuan-MT-Chimera-7B:Q8" 

#print('--- plugin GIGA: '+str(plugins),GIGA_TOKEN,URL_OLLAMA)
# Добавить проверку на роль 
# try:
#     GIGA_TOKEN = plugins.get("GIGA_CHAT")
# except Exception as e:
#     GIGA_TOKEN = ''
#logger.info('--- plugin GIGA: '+str(get_plugins('GIGA')))
# Вынести на параметр сделать возможность запоминать или изменять для каждого пользователя отдельно.
# content="Ты бот супер программист на питон, который помогает пользователю провести время с пользой."


# def get_image():
#     if URL_OLLAMA == '':
#         return  'URL_OLLAMA is empty', [], {}
#     API_URL = f"{URL_OLLAMA}/api/generate"

#     payload = {
#         "model": "ozbillwang/stable_diffusion-ema-pruned-v2-1_768.q8_0:latest",                     # или stable-diffusion / flux
#         "prompt": "A surreal portrait of a cyber‑punk cat, vivid colors",
#         "options": {
#             "num_predict": 1,
#             "width": 1024,
#             "height": 1024,
#             "seed": 777,
#         },
#         # Для SD необходимо явно указать, что хотим изображение:
#         "stream": False,
#         "format": "json"
#     }

#     r = requests.post(API_URL, json=payload, timeout=180)   # генерация может занять ~30‑60 сек
#     r.raise_for_status()
#     data = r.json()

#     # В ответе будет поле `image` (base64‑строка)
#     if "image" in data:
#         img = base64.b64decode(data["image"])
#         Path("sdxl_result.png").write_bytes(img)
#         print("✅ Сохранено → sdxl_result.png")
#     else:
#         print("❌ Ошибка:", data)


import requests
import json
import argparse
import sys
import codecs
import logging

# Установка кодировки UTF-8 для вывода в консоль
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# python tgbot/plugins/chat_translate.py --text "Привет, мир!" --from "ru" --to "en" --model "lauchacarro/qwen2.5-translator:latest"
# python tgbot/plugins/chat_translate.py -t "Bonjour le monde"
def translate_with_ollama(text, model="lauchacarro/qwen2.5-translator:latest", src_lang="auto", target_lang="ru",url_ollama="http://127.0.0.1:11434"):
    """
    Функция для перевода текста с помощью Ollama
    """
    try:
        # URL для API Ollama
        url = url_ollama + "/api/generate"
        
        # Подготовка данных для запроса
        data = {
            "model": model,
            "prompt": f"Translate the following text from {src_lang} to {target_lang}: {text}",
            "stream": False
        }
        
        # Отправка запроса
        response = requests.post(url, json=data,timeout=30000)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Успешный перевод с {src_lang} на {target_lang}" )
            return result.get("response", "Не удалось получить перевод")
        else:
            logger.error(f"Ошибка при обращении к Ollama: {response.status_code} {response.text}")
            return f"Ошибка при обращении к Ollama: {response.text}"
    except Exception as e:
        logger.error(f"Ошибка при переводе: {str(e)}")
        return f"Ошибка при переводе: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description='Перевод текста с помощью Ollama и модели lauchacarro/qwen2.5-translator:latest')
    parser.add_argument('--text', '-t', required=True, help='Текст для перевода')
    parser.add_argument('--model', '-m', default='lauchacarro/qwen2.5-translator:latest', help='Модель Ollama для перевода (по умолчанию: lauchacarro/qwen2.5-translator:latest)')
    parser.add_argument('--from', '-f', dest='src_lang', default='auto', help='Исходный язык (по умолчанию: auto)')
    parser.add_argument('--to', '-to', default='ru', help='Целевой язык (по умолчанию: ru)')
    parser.add_argument('--no-log', action='store_true', help='Отключить логгирование')
    parser.add_argument('--url', '-u', dest='url_ollama', default='http://localhost:11434', help='Адрес Ollama (по умолчанию: http://localhost:11434)')

    args = parser.parse_args()
    
    # Получаем перевод
    translation = translate_with_ollama(args.text, args.model, args.src_lang, args.to, args.url_ollama)
    
    # Выводим результат
    if not args.no_log:
        print(f"Перевод с {args.src_lang} на {args.to} с использованием модели {args.model}:")
    print(translation)


if __name__ == "__main__":
    main()