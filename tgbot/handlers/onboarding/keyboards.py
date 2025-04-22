from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON
from tgbot.handlers.onboarding.static_text import github_button_text, secret_level_button_text
from dtb.settings import get_plugins

def make_keyboard_for_start_command(roles) -> InlineKeyboardMarkup:
    plugins = get_plugins(roles)
    # Количество колонок (количество кнопок в одном ряду)
    columns = 4
    # Создание клавиатуры
    keyboard = []
    row = []  # Текущий ряд кнопок
    for pl,val in plugins.items():
        print('--',pl,val)
        row.append(InlineKeyboardButton(str(pl), callback_data=str(pl)))
        if len(row) == columns:
            keyboard.append(row)
            row = []
    if row:  # Если остались неиспользованные кнопки, добавляем последний ряд
        keyboard.append(row)
    '''
    buttons = [[
        InlineKeyboardButton("MSWsss ssss "+chr(13)+chr(10)+"zzzzz zzzzz", callback_data="button1",),
        ],[
        InlineKeyboardButton("📌W", url="https://gitlab.com/sergeymi/test/-/issues/?sort=updated_desc&state=opened&first_page_size=100"),
        InlineKeyboardButton("Mddddd ddddd dddddd ddddddddd dddddSW", url="https://gitlab.com/sergeymi/test/-/issues/?sort=updated_desc&state=opened&first_page_size=100"),
        ],[
        InlineKeyboardButton("reports-gitlab-telebot", url="https://github.com/SergeyMi37/reports-gitlab-telebot"),
        #InlineKeyboardButton(secret_level_button_text, callback_data=f'{SECRET_LEVEL_BUTTON}')
    ]]
   '''
    return InlineKeyboardMarkup(keyboard)
