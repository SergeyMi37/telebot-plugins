from typing import Dict
from telegram import Update

def get_tele_command(update: Update) -> str:
   #print('---update:---',update)
   try:
      if update.message.text:
         return update.message.text, update.message
      else:
         return update.edited_message.text, update.message
   except Exception as err:
      #print("---err-get_tele_command-",err)
      return update.edited_message.text, update.edited_message

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
