from typing import Dict
from telegram import Update
import pprint as pp
from dtb.settings import settings

def get_tele_command(update: Update) -> str:
   #print('----get_tele_command---',update)
   from users.models import Updates
   if settings.get("UPDATES_DB"):
      #pp.pprint(update.to_dict(), depth=2)
      update_obj = Updates.save_from_update(update)
   #pp.pprint(update_obj, depth=2)
   try:
      if update.message:
         upms = update.message
      elif update.edited_message:
         upms = update.edited_message
      elif not update:
         upms = None
      else:
         upms = update.callback_query.message
   except Exception as err:
      pp.pprint('⚠️---',update)
      upms = None
    # todo send log
   
   return upms # upms.chat, upms.from_user


def extract_user_data_from_update(update: Update) -> Dict:
   """ python-telegram-bot's Update instance --> User info """
   upms = get_tele_command(update)
   try:
      user = update.effective_user.to_dict()
   except Exception as e:
      try:
         user = upms.from_user.to_dict()
      except Exception as e:
         print(f'-----Произошла ошибка----effective_user--{e}',update)
   if upms is None:
      return None
   return dict(
        user_id=user["id"],
        #is_blocked_bot=False,   # был сброс блокировки
        **{
            k: user[k]
            for k in ["username", "first_name", "last_name", "language_code"]
            if k in user and user[k] is not None
        },
    )

