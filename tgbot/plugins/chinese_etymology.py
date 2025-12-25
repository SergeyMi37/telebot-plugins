import os
import sys
import codecs
import argparse

# Установка кодировки UTF-8 для вывода в консоль
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Установка переменных окружения для отключения прокси перед импортом selenium
# os.environ['http_proxy'] = ''
# os.environ['https_proxy'] = ''
# os.environ['HTTP_PROXY'] = ''
# os.environ['HTTPS_PROXY'] = ''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import logging

from webdriver_manager.chrome import ChromeDriverManager

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
    
    # Настройка опций Chrome
    chrome_options = Options()
    if not verbose:
        chrome_options.add_argument("--headless")  # Запуск в фоновом режиме (без GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # Отключение использования прокси
    chrome_options.add_argument("--no-proxy-server")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-features=NetworkService,NetworkServiceInProcess")
    chrome_options.add_argument("--no-experiments")
    chrome_options.add_argument("--no-ping")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-log-file")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-gpu")
    
    # Используем webdriver-manager для автоматического управления версиями ChromeDriver
    
    # if os.path.exists("chromedriver.exe"):
    #     service = Service("chromedriver.exe")
    #     service.args = ['--no-proxy-server', '--proxy-server="direct://"', '--disable-features=NetworkService,NetworkServiceInProcess']
    #     logger.info("Использование ChromeDriver из текущей директории")
    # else:
    #     logger.info("Использование ChromeDriver из системного PATH")
    
    logger = setup_logging(verbose)
    try:
        # Инициализация драйвера с явным указанием пути к ChromeDriver info: chrome=143.0.7499.170)
        service = Service(ChromeDriverManager().install())
        if service:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome драйвер успешно инициализирован")
    except Exception as e:
        msg = f"Ошибка при инициализации Chrome драйвера: {e} Возможно, ChromeDriver не установлен или не найден в PATH. Пожалуйста, убедитесь, что ChromeDriver установлен и доступен"
        if verbose:  # Показываем ошибку только если логгирование включено
            logger.error(msg)
        return (500,msg)
    
    try:
        # Открытие сайта с поиском иероглифа
        url = f"https://www.archchinese.com/chinese_english_dictionary.html?find={character}"
        logger.info(f"Открытие URL: {url}".encode('utf-8', errors='ignore').decode('utf-8'))
        driver.get(url)
        
        # Ожидание загрузки страницы
        wait = WebDriverWait(driver, 2)
        
        # Поиск кнопки "More Etymology Information"
        logger.info("Поиск кнопки 'More Etymology Information'")
        # <a class="btn btn-default circle-link blue-text" href="javascript:void(0)" onclick="event.preventDefault(); fn_showCharEtymology(0);">&nbsp;&nbsp;&nbsp;&nbsp;<i class="fa fa-angle-double-down"></i>&nbsp;More Etymology Information&nbsp;&nbsp;&nbsp;</a>
        more_etymology_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-default.circle-link.blue-text[onclick*='fn_showCharEtymology']"))
        )
        # print(more_etymology_button)
        # Клик по кнопке
        logger.info("Клик по кнопке 'More Etymology Information'")
        more_etymology_button.click()
        
        # Ожидание появления дополнительной информации
        logger.info("Ожидание появления информации об этимологии")
        
        # После клика на кнопку может потребоваться время для загрузки информации
        # Подождем фиксированное время, а затем проверим, появилась ли информация
        time.sleep(2)
        
        # Поиск элементов, содержащих информацию об этимологии
        # Сначала ищем основной элемент gwt-Tree
        etymology_elements = driver.find_elements(By.CSS_SELECTOR, ".gwt-Tree")
        
        # Если не найден элемент с классом gwt-Tree, ищем другие возможные элементы
        if not etymology_elements:
            etymology_elements = driver.find_elements(By.CSS_SELECTOR, ".gwt-TreeItem")
        
        # Также ищем элементы с текстом, связанным с этимологией
        if not etymology_elements:
            etymology_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'etymology') or contains(text(), 'origin') or contains(text(), 'ancient') or contains(text(), 'Evolution') or contains(text(), 'History')]")
        
        # Получение текста дополнительной информации
        etymology_text = ""
        if etymology_elements:
            for element in etymology_elements:
                etymology_text += element.text + "\n"
        else:
            # Если не найдены элементы с указанными классами или текстом, ищем внутри body
            body_element = driver.find_element(By.TAG_NAME, "body")
            etymology_text = body_element.text
        
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
        
        #logger.info("Информация об этимологии успешно получена")
        #return (200, etymology_text)
        
    except Exception as e:
        error_message = "Ошибка при получении информации об этимологии: " + str(e)
        if verbose:  # Показываем ошибку только если логгирование включено
            logger.error(f"{error_message}")
        return (500, error_message)
        
    finally:
        # Закрытие браузера
        if 'driver' in locals():
            if verbose:  # Показываем сообщение только если логгирование включено
                logger.info("Закрытие браузера")
            driver.quit()

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