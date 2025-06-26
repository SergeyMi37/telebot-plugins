"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from typing import Union, List, Optional, Dict

import telegram

from dtb.celery import app
from celery.utils.log import get_task_logger
from tgbot.handlers.broadcast_message.utils import send_one_message, from_celery_entities_to_entities, \
    from_celery_markup_to_markup
from users.models import User
from tgbot.plugins import reports_gitlab, servers_iris

logger = get_task_logger(__name__)

@app.task(ignore_result=True)
def broadcast_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            send_one_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")

# Если есть доступ к плагину Issue Time tracking
@app.task(ignore_result=True)
def broadcast_gitlb_daily_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ Используется для трансляции сообщений пользователям в соответсвии с их ролями."""
    logger.info(f"Собираюсь отправить сообщение: '{text}' для {len(user_ids)} пользователей users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    logger.info(f"Получим ид пользователей : '{user_ids[0]}")
    res = ''
    '''  Если есть условие в первом поле UserId, проверяем на его сработку, есть да, то смотрим для каких Ролей, эта сработка
    if 'Condition(' in user_ids[0]: # Получение условия
        cond = user_ids[0].split('Condition(')[1].split(')')[0]
        res = servers_iris.command_server(cond)
        print('--== res =',res)
        if '<b>Err</b>' in res: # Нужно послать сообщение пользователям
            pass
        else:
            logger.info("Сообщение не послано пользователям")
            return
        Если пересечение не пустое, то добавляем пользователя в новый список, по которому и будем посылать сообщения
        Реализовано в проекте https://github.com/SergeyMi37/reports-iris-telebot.git
    '''

    if 'Roles(' in user_ids[0]: # Получение пользователей по ролям
        roles = user_ids[0].split('Roles(')[1].split(')')[0].split(",") # Все роли через запятую в первом ИД пользователя
        #print('--- Роли, которые должны быть у пользователей, которым посылать сообщения ',roles)
        logger.info(f"Роли, которые должны быть у пользователей, которым посылать сообщения : '{roles}")
        _user_ids = list(User.objects.filter(is_blocked_bot=False).values_list('user_id', flat=True)) # Получим всех реальных пользователей в джанге
        for id in _user_ids:
            u = User.get_user_by_username_or_user_id(id)
            _roles = u.roles
            print('-ИД;',id,_roles)
            if _roles:
                _rol = _roles.split(",")
                print('--ИД;',id,roles,_rol,set(roles).intersection(_rol))
                if set(roles).intersection(_rol): # Пересечение списков ролей у пользователя и Roles( должно быть не пустым 
                    print('---OK;')
                    try:
                        # Сохраните в табеле ежедневный отчет ---  https://git.lab.nexus/ctz/lab/tabel/-/issues/?sort=updated_desc&state=opened&label_name%5B%5D={pro_ru}&first_page_size=20 --- И проверьте командой /daily_{pro_en}
                        pro_ru = _rol[0]
                        pro_en = reports_gitlab.lab_replay(pro_ru,"ru_en")
                        msg = text.replace("{pro_ru}",pro_ru).replace("{pro_en}",pro_en)
                        print('---ИД;',msg)
                        send_one_message(
                            user_id = id,
                            text = msg,
                            entities = entities_,
                            parse_mode = parse_mode,
                            reply_markup = reply_markup_,
                        )
                        logger.info(f"Сообщение {msg} было отправлено {id}")
                    except Exception as e:
                        logger.error(f"не удалось отправить сообщение {id}, причина: {e}")
                    time.sleep(max(sleep_between, 0.1))

    logger.info("Трансляция завершена!")

# Если есть доступ к плагину IRIS
@app.task(ignore_result=True)
def broadcast_custom_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ Используется для трансляции сообщений большому количеству пользователей. """
    logger.info(f"Собираюсь отправить сообщение: '{text}' для {len(user_ids)} пользователей users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    print('--- user_ids ',type(user_ids),user_ids[0])
    res = ''
    if 'Condition(' in user_ids[0]: # Получение условия
        cond = user_ids[0].split('Condition(')[1].split(')')[0]
        res = servers_iris.command_server(cond)
        print('--== res =',res)
        if '<b>Error</b>' in res: # Нужно послать сообщение пользователям в  следующим блоке
            pass
        else:
            logger.info("Сообщение не послано пользователям")
            return
    if 'Roles(' in user_ids[0]: # Получение пользователей по ролям, чтоб послать сообщение
        roles = user_ids[0].split('Roles(')[1].split(')')[0].split(",")
        print('--- Роли, которые должны быть у пользователей, которым посылать сообщения ',roles)
        _user_ids = list(User.objects.filter(is_blocked_bot=False).values_list('user_id', flat=True))
        for id in _user_ids:
            u = User.get_user_by_username_or_user_id(id)
            _roles = u.roles
            if _roles:
                _rol = _roles.split(",")
                if set(roles).intersection(_rol): # Пересечение списков ролей должно быть не пустым
                    if id not in user_ids:
                        user_ids.append(id)
    print('--==-',user_ids)
    for user_id in user_ids:
        try:
            if not isinstance(user_id, int):
                continue
            send_one_message(
                user_id=user_id,
                text=text + '\n' + res,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Широковещательное сообщение было отправлено {user_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение {user_id}, причина: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Трансляция завершена!")
