# dtb/middleware.py
from django.conf import settings

class DisableCSRFForWebhook:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем путь вебхука из настроек
        webhook_path = getattr(settings, 'WEBHOOK_SECRET_PATH', '').strip('/')
        
        # Если запрос идет на путь вебхука - отключаем CSRF
        if webhook_path and request.path.startswith('/' + webhook_path):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        return self.get_response(request)