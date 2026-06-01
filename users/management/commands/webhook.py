# tgbot/management/commands/manage_webhook.py
"""
Управление вебхуками Telegram через Django management command

Использование:
    python manage.py manage_webhook set
    python manage.py manage_webhook delete
    python manage.py manage_webhook info
    python manage.py manage_webhook --help
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Управление вебхуками Telegram бота'
    
    # Цветовые стили для вывода
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['set', 'delete', 'info'],
            help='Действие с вебхуком: установить, удалить или получить информацию'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительное выполнение (игнорировать предупреждения)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано, но не выполнять'
        )
        
        parser.add_argument(
            '--url',
            type=str,
            help='Пользовательский URL для вебхука (переопределяет настройки)'
        )
        
        parser.add_argument(
            '--max-connections',
            type=int,
            default=40,
            help='Максимальное количество одновременных соединений (по умолчанию 40)'
        )
        
        parser.add_argument(
            '--allowed-updates',
            type=str,
            nargs='+',
            default=['message', 'callback_query', 'inline_query'],
            help='Типы обновлений для приема'
        )

    def handle(self, *args, **options):
        action = options['action']
        force = options['force']
        dry_run = options['dry_run']
        
        # Проверяем режим работы бота
        bot_mode = getattr(settings, 'BOT_MODE', 'polling')
        
        if action == 'set' and bot_mode != 'webhook' and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Бот работает в режиме {bot_mode.upper()}, а не webhook.\n'
                    f'Установка вебхука в этом режиме может вызвать конфликты.\n'
                    f'Используйте --force если уверены.'
                )
            )
            return
        
        # Выполняем действие
        if dry_run:
            self._dry_run(action, options)
            return
        
        try:
            if action == 'set':
                self._set_webhook(options)
            elif action == 'delete':
                self._delete_webhook(options)
            elif action == 'info':
                self._get_webhook_info(options)
        except TelegramError as e:
            raise CommandError(f'Ошибка Telegram API: {e}')
        except Exception as e:
            raise CommandError(f'Неожиданная ошибка: {e}')
    
    def _set_webhook(self, options):
        """Установка вебхука"""
        self.stdout.write('🔄 Установка вебхука...')
        
        # Получаем URL
        if options['url']:
            webhook_url = options['url']
        else:
            domain = getattr(settings, 'DOMAIN', None)
            if not domain:
                raise CommandError(
                    'Не задан DOMAIN в настройках. Укажите его в .env или используйте --url'
                )
            
            webhook_path = getattr(
                settings, 
                'WEBHOOK_SECRET_PATH', 
                'super_secter_webhook/'
            )
            webhook_path = webhook_path.strip('/')
            webhook_url = f"https://{domain}/{webhook_path}/"
        
        self.stdout.write(f'📍 URL вебхука: {webhook_url}')
        
        # Проверяем URL
        if not webhook_url.startswith('https://'):
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Внимание: вебхук должен использовать HTTPS!'
                )
            )
            if not options['force']:
                return
        
        # Создаем бота
        token = settings.TELEGRAM_TOKEN
        bot = Bot(token=token)
        
        # Проверяем текущий вебхук
        current_info = bot.get_webhook_info()
        if current_info.url and current_info.url != webhook_url:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Текущий вебхук: {current_info.url}\n'
                    f'Будет заменен на: {webhook_url}'
                )
            )
        
        # Устанавливаем вебхук
        result = bot.set_webhook(
            url=webhook_url,
            max_connections=options['max_connections'],
            allowed_updates=options['allowed_updates']
        )
        
        if result:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Вебхук успешно установлен!')
            )
            
            # Проверяем установку
            info = bot.get_webhook_info()
            self.stdout.write(f'\n📊 Информация о вебхуке:')
            self.stdout.write(f'   URL: {info.url}')
            self.stdout.write(f'   Max connections: {options["max_connections"]}')
            
            # Логируем в файл
            logger.info(f'Webhook set to {webhook_url}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Не удалось установить вебхук')
            )
            logger.error(f'Failed to set webhook to {webhook_url}')
    
    def _delete_webhook(self, options):
        """Удаление вебхука"""
        self.stdout.write('🔄 Удаление вебхука...')
        
        token = settings.TELEGRAM_TOKEN
        bot = Bot(token=token)
        
        # Проверяем текущий вебхук
        current_info = bot.get_webhook_info()
        if not current_info.url:
            self.stdout.write(
                self.style.WARNING('⚠️  Вебхук уже удален или не установлен')
            )
            return
        
        self.stdout.write(f'📍 Текущий вебхук: {current_info.url}')
        
        if not options['force']:
            confirm = input('Удалить вебхук? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('❌ Операция отменена')
                return
        
        # Удаляем вебхук
        result = bot.delete_webhook()
        
        if result:
            self.stdout.write(
                self.style.SUCCESS('✅ Вебхук успешно удален')
            )
            logger.info('Webhook deleted')
            
            # Проверяем удаление
            info = bot.get_webhook_info()
            self.stdout.write(f'📊 Текущий вебхук: {info.url or "Не установлен"}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Не удалось удалить вебхук')
            )
            logger.error('Failed to delete webhook')
    
    def _get_webhook_info(self, options):
        """Получение информации о вебхуке"""
        self.stdout.write('🔄 Получение информации о вебхуке...')
        
        token = settings.TELEGRAM_TOKEN
        bot = Bot(token=token)
        
        try:
            info = bot.get_webhook_info()
            
            self.stdout.write('\n📊 ИНФОРМАЦИЯ О ВЕБХУКЕ\n' + '='*50)
            
            # Основная информация
            self.stdout.write(f'🔗 URL: {info.url or "❌ Не установлен"}')
            self.stdout.write(f'🔒 SSL сертификат: {"Да" if info.has_custom_certificate else "Нет"}')
            self.stdout.write(f'📨 Ожидающих обновлений: {info.pending_update_count}')
            self.stdout.write(f'🔌 Макс. соединений: {info.max_connections or 40}')
            
            # Ошибки
            if info.last_error_date:
                from datetime import datetime
                error_date = datetime.fromtimestamp(info.last_error_date)
                self.stdout.write(
                    self.style.ERROR(
                        f'\n❌ Последняя ошибка:'
                    )
                )
                self.stdout.write(f'   Дата: {error_date}')
                self.stdout.write(f'   Сообщение: {info.last_error_message}')
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Ошибок не обнаружено')
                )
            
            # Разрешенные типы обновлений
            if info.allowed_updates:
                self.stdout.write(f'\n📝 Разрешенные типы: {", ".join(info.allowed_updates)}')
            else:
                self.stdout.write(f'\n📝 Разрешенные типы: Все')
            
            # IP адрес (если есть)
            if info.ip_address:
                self.stdout.write(f'🌐 IP адрес: {info.ip_address}')
            
            logger.info('Webhook info retrieved successfully')
            
        except TelegramError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка получения информации: {e}')
            )
            logger.error(f'Failed to get webhook info: {e}')
    
    def _dry_run(self, action, options):
        """Режим имитации (dry run)"""
        self.stdout.write('\n🔍 РЕЖИМ ИМИТАЦИИ (dry-run)\n' + '='*50)
        
        if action == 'set':
            self.stdout.write('Будет выполнено: Установка вебхука')
            
            if options['url']:
                webhook_url = options['url']
            else:
                domain = getattr(settings, 'DOMAIN', 'localhost')
                webhook_path = getattr(
                    settings, 
                    'WEBHOOK_SECRET_PATH', 
                    'super_secter_webhook/'
                ).strip('/')
                webhook_url = f"https://{domain}/{webhook_path}/"
            
            self.stdout.write(f'📍 URL: {webhook_url}')
            self.stdout.write(f'🔌 Max connections: {options["max_connections"]}')
            self.stdout.write(f'📝 Allowed updates: {options["allowed_updates"]}')
            
        elif action == 'delete':
            self.stdout.write('Будет выполнено: Удаление вебхука')
            
            # Показываем текущий вебхук если можем
            try:
                token = settings.TELEGRAM_TOKEN
                bot = Bot(token=token)
                info = bot.get_webhook_info()
                if info.url:
                    self.stdout.write(f'📍 Будет удален: {info.url}')
                else:
                    self.stdout.write('📍 Вебхук не установлен')
            except:
                self.stdout.write('📍 Не удалось получить текущий вебхук')
                
        elif action == 'info':
            self.stdout.write('Будет выполнено: Получение информации о вебхуке')
        
        self.stdout.write('\n✨ Чтобы выполнить реальные действия, уберите --dry-run')