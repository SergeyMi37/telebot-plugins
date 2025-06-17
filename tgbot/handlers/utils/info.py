from typing import Dict
from telegram import Update


def get_tele_command(update: Update) -> str:
   #print('----get_tele_command---',update)
   try:
      if update.message:
         upms = update.message
      elif update.edited_message:
         upms = update.edited_message
      else:
         upms = update.callback_query.message
   except Exception as err:
      upms = update.edited_message
   #text = upms.text
   chat = upms.chat
   from_user = upms.from_user
   # todo send log
   return upms, chat, from_user


def extract_user_data_from_update(update: Update) -> Dict:
   """ python-telegram-bot's Update instance --> User info """
   try:
      user = update.effective_user.to_dict()
   except Exception as e:
      print(f'-----Произошла ошибка----effective_user--{e}',update)
   
   return dict(
        user_id=user["id"],
        #is_blocked_bot=False,   # был сброс блокировки
        **{
            k: user[k]
            for k in ["username", "first_name", "last_name", "language_code"]
            if k in user and user[k] is not None
        },
    )
