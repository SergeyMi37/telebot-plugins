import os
import sys
import codecs
import argparse

# Установка кодировки UTF-8 для вывода в консоль
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Установка переменных окружения для отключения прокси перед импортом playwright
# Убираем установку переменных окружения, т.к. они могут конфликтовать с Playwright
# os.environ['http_proxy'] = ''
# os.environ['https_proxy'] = ''
# os.environ['HTTP_PROXY'] = ''
# os.environ['HTTPS_PROXY'] = ''

# os.environ['OPENSSL_CONF']='/etc/ssl/openssl.cnf'
# os.environ['SSL_CERT_FILE']='/etc/ssl/certs/ca-certificates.crt'
# os.environ['NODE_EXTRA_CA_CERTS']='/etc/ssl/certs/ca-certificates.crt'

from playwright.sync_api import sync_playwright
import logging

# Настройка логгирования
def setup_logging(verbose=True):
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def get_character_etymology(character, verbose=True):
    """
    Получает дополнительную информацию об этимологии китайского иероглифа
    с использованием сайта https://www.archchinese.com/
    Возвращает кортеж: (статус, текст)
    Статус 200 - успех, другой код - ошибка
    """
    # Проверка character на пустоту и на китайский иероглиф
    if not character:
        if verbose:
            print("Ошибка: Параметр character не может быть пустым")
        return (400, "Параметр character не может быть пустым")
    
    # Проверка, что строка содержит китайский иероглиф
    # Китайские иероглифы находятся в диапазонах Unicode: \u4e00-\u9fff
    import re
    if not re.search(r'[\u4e00-\u9fff]', character):
        if verbose:
            print(f"Ошибка: '{character}' не содержит китайских иероглифов")
        return (400, f"'{character}' не содержит китайских иероглифов")
    
    # Проверка, что строка содержит только один иероглиф
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', character)
    if len(chinese_chars) != 1:
        if verbose:
            print(f"Ошибка: '{character}' должен содержать только один китайский иероглиф")
        return (400, f"'{character}' должен содержать только один китайский иероглиф")
    
    logger = setup_logging(verbose)
    logger.info(f"Начало поиска этимологии для иероглифа: {character}".encode('utf-8', errors='ignore').decode('utf-8'))
    
    with sync_playwright() as p:
        # Настройка аргументов браузера
        # Запуск браузера
        browser = p.chromium.launch(
            headless=not verbose,  # Запуск в фоновом режиме если не verbose
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-default-apps",
                "--disable-features=NetworkService,NetworkServiceInProcess",
                "--no-experiments",
                "--no-ping",
                "--no-first-run",
                "--disable-logging",
                "--log-level=3",
                "--silent",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--disable-background-networking",
                "--disable-ipc-flooding-protection",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ],
            ignore_default_args=["--enable-automation"],
            # Установка времени ожидания
            slow_mo=100  # Добавим небольшую задержку для более стабильной работы
        )
        # Создание новой страницы с настройками прокси
        # Настройка контекста с увеличенным таймаутом и дополнительными опциями
        page = browser.new_page()
        page.set_default_timeout(120000) #60000)  # Установим таймаут 60 секунд
        
        # Установка дополнительных заголовков для имитации обычного браузера
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        logger.info("Chrome браузер успешно инициализирован")
        
        try:
            # Открытие сайта с поиском иероглифа
            url = f"https://www.archchinese.com/chinese_english_dictionary.html?find={character}"
            logger.info(f"Открытие URL: {url}".encode('utf-8', errors='ignore').decode('utf-8'))
            page.goto(url, wait_until="domcontentloaded")
            
            # Ожидание загрузки страницы
            page.wait_for_load_state("networkidle")
            
            # Поиск кнопки "More Etymology Information"
            logger.info("Поиск кнопки 'More Etymology Information'")
            # <a class="btn btn-default circle-link blue-text" href="javascript:void(0)" onclick="event.preventDefault(); fn_showCharEtymology(0);">&nbsp;&nbsp;&nbsp;<i class="fa fa-angle-double-down"></i>&nbsp;More Etymology Information&nbsp;&nbsp;&nbsp;</a>
            more_etymology_button = page.wait_for_selector("a.btn.btn-default.circle-link.blue-text[onclick*='fn_showCharEtymology']", timeout=30000)  # Увеличим таймаут до 30 секунд
            # Клик по кнопке
            logger.info("Клик по кнопке 'More Etymology Information'")
            more_etymology_button.click()
            
            # Ожидание появления дополнительной информации
            logger.info("Ожидание появления информации об этимологии")
            
            # После клика на кнопку может потребоваться время для загрузки информации
            page.wait_for_timeout(2000)
            
            # Поиск элементов, содержащих информацию об этимологии
            # Сначала ищем основной элемент gwt-Tree
            etymology_elements = page.query_selector_all(".gwt-Tree")
            
            # Если не найден элемент с классом gwt-Tree, ищем другие возможные элементы
            if not etymology_elements:
                etymology_elements = page.query_selector_all(".gwt-TreeItem")
            
            # Также ищем элементы с текстом, связанным с этимологией
            if not etymology_elements:
                # В Playwright нет прямого эквивалента XPATH по тексту, поэтому используем CSS селекторы и фильтрацию
                all_elements = page.query_selector_all("*")
                etymology_elements = []
                for element in all_elements:
                    text_content = element.text_content()
                    if any(keyword in text_content.lower() for keyword in ['etymology', 'origin', 'ancient', 'evolution', 'history']):
                        etymology_elements.append(element)
            
            # Получение текста дополнительной информации
            etymology_text = ""
            if etymology_elements:
                for element in etymology_elements:
                    etymology_text += element.text_content() + "\n"
            else:
                # Если не найдены элементы с указанными классами или текстом, ищем внутри body
                body_element = page.query_selector("body")
                etymology_text = body_element.text_content() if body_element else ""
            
            # Если так и не удалось найти информацию об этимологии, выводим сообщение
            if not etymology_text.strip():
                logger.warning("Не удалось найти информацию об этимологии")
                etymology_text = "Информация об этимологии не найдена"
            
            # Вывод результата с обработкой кодировки
            try:
                print(f"Дополнительная информация об этимологии иероглифа '{character}':")
                print(etymology_text)
            except UnicodeEncodeError:
                # Если возникает ошибка кодировки, выводим информацию в закодированном виде
                print(f"Дополнительная информация об этимологии иероглифа '{character}':".encode('utf-8', errors='ignore').decode('utf-8'))
                print(etymology_text.encode('utf-8', errors='ignore').decode('utf-8'))
            
            # Возвращаем результат с обработкой кодировки
            try:
                return (200, etymology_text)
            except UnicodeEncodeError:
                return (200, etymology_text.encode('utf-8', errors='ignore').decode('utf-8'))
            
        except Exception as e:
            error_message = "Ошибка при получении информации об этимологии: " + str(e)
            if verbose:  # Показываем ошибку только если логгирование включено
                logger.error(f"{error_message}")
            return (500, error_message)
            
        finally:
            # Закрытие браузера
            if 'browser' in locals():
                if verbose:  # Показываем сообщение только если логгирование включено
                    logger.info("Закрытие браузера")
                browser.close()

def main():
    parser = argparse.ArgumentParser(description='Получение информации об этимологии китайских иероглифов')
    parser.add_argument('--character', '-c', default='牛', help='Китайский иероглиф для поиска (по умолчанию: 牛)')
    parser.add_argument('--no-log', action='store_true', help='Отключить логгирование')
    
    args = parser.parse_args()
    
    # Проверки на пустоту и китайский иероглиф теперь находятся внутри функции get_character_etymology
    
    # Получаем информацию об этимологии
    status, result = get_character_etymology(args.character, verbose=not args.no_log)
    
    # Выводим результат, если логгирование включено
    
    if status == 200:
        print(f"Дополнительная информация об этимологии иероглифа '{args.character}':")
        print(result)
    else:
        print(f"Ошибка при получении информации об этимологии (код {status}): {result}")

if __name__ == "__main__":
    main()