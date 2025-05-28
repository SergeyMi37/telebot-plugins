# Plugin for reporting from servers IRIS
# Name Plugin: IRIS

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from tgbot.handlers.admin import static_text
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
#from tgbot.handlers.utils.decorators import admin_only, send_typing_action
from tgbot.handlers.utils.decorators import check_blocked_user
from tgbot.handlers.utils.date_utils import tz_to_moscow
from users.models import User
from tgbot.handlers.admin.static_text import BR
import os
from pathlib import Path
from typing import Any
#import datetime
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dtb.settings import get_plugins
import requests
import json

from openpyxl import Workbook
from dtb.settings import logger

TIMEOUT =25

# Добавить проверку на роль 
#plugin
plugins_iris = get_plugins('').get('IRIS')
#logger.info('--- plugin IRIS: '+str(plugins_iris))
#logger.info('--=- plugin IRIS: '+str(plugin))

#for key in plugins_iris:
  #print('-- ',key,plugins_iris[key])

@check_blocked_user
def command_servers(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    if not u.is_admin:
        update.message.reply_text(static_text.only_for_admins)
        return
    telecmd, upms = get_tele_command(update)

    result=''
    for key in plugins_iris:
    #for key in os.environ:
      if "URL_" in key:
        #print(key, '=>', os.environ[key])
        #result += key.split("URL_")[1]
        #Загрузить из сервиса результат
        #_u = os.environ[key]+'1'
        #print('---url---',_u )
        _u = plugins_iris[key]+'1'
        err, resp = get_open(url=_u,timeout=TIMEOUT) # 0 - Только статус
        #print(err, resp) 
      
        if err.find("_OK")!=-1:
           icon = "🟡 /" 
           count = len(resp["ns"]) if "ns" in resp else 0
           msg= f'<b>{resp["server"]}</b> Продукций: {count}'
        else:
           icon = "🔴 "
           msg = "Нет доступа"
        #
        result += f'{icon}s_{key.split("URL_")[1]} {msg}{BR}'
    upms.reply_text(
            text=result,
            parse_mode=ParseMode.HTML,
        )

def get_open(url: str, timeout:int = 3
        ) -> tuple[int, Any]:

  o = urlparse(url)
  #print('---',o.netloc,o.username,o.password)

  errno = "code.CODE_GET_OK"
  headers = {
        'Accept': 'application/json;odata=verbose',
        }
  auth=(o.username,o.password)
  #Если не включает @, то взять всю строку, если нет, то Последнее поле по @
  _host = o.netloc if o.netloc.find("@")==-1  else  o.netloc.split("@")[-1] 
  _url = f'{o.scheme}://{_host}{o.path}'
  #print('--get_open--',_url,auth)
  try:
      response = requests.get(_url,verify=False,headers=headers,timeout=timeout,auth=auth)
      if response.status_code == 200:
        answer = json.loads(response.text)
        return "code.CODE_GET_OK", answer
      elif response.status_code == 404:
        return "code.CODE_GET_EMPTY", None
      else:
        errno = "code.CODE_GET_FAIL"
        answer = {
          "errno": errno,
          'err_message': '{0:s}:{1:s}'.format(errno, response.text)
        }
        raise Exception(answer.get('err_message'))
  except Exception as e:
    errno = "code.CODE_GET_FAIL"
    answer = {
      "errno": errno,
      'err_message': '{0}:{1}'.format(errno, e.args.__repr__())
    }
    return errno, answer

def command_server(cmd: str) -> None:
    '''
    Функция разбора суфикса команды вида "ИмяСервера_ИмяОбласти_1параметр_2параметр"
    Если "ИмяСервера_SYS__" выводить информацию по журналированияю и дисковому пространству
    Если "ИмяСервера___" выводить список продукций с количеством ошибок за 1 день
    Если "ИмяСервера_ИмяОбласти__" выводить список первых 20 ошибок с усеченным текстом
    '''
    #url = os.getenv(f'URL_{cmd.split("_")[0]}')
    url = plugins_iris.get(f'URL_{cmd.split("_")[0]}')
    result=''
    _servname = cmd.split("_")[0]
    if not url:
      msg = "🔴 Нет сервера "+ _servname
      result += f'{msg}{BR} /help'
      return result

    #if cmd.split("_")[2]: #если есть параметр 1
  
    if cmd.split("_")[1]: #если есть NameSpace
       _ns = cmd.split("_")[1] if cmd.split("_")[1].find('-')!=-1 else cmd.split("_")[1].replace("v","-")
       if _ns=='CC':
          cc = f'CC_{_servname}_{cmd.split("_")[2]}'
          #logger.info(cc)
          _urlcc = plugins_iris.get(cc, "")
          if _urlcc:
             err, resp = get_open(url=_urlcc,timeout=TIMEOUT)
             #print('---=-',err,type(resp), resp)
             result +=f'Статус:<b>{resp["status"]}</b>\n'
             if resp.get("array",''):
              for arr in resp["array"]:
                ic = arr['icon'] 
                if ic=='y':
                  ic = "🟡"
                elif ic=='r':
                  ic = "🔴"
                elif ic=='g':
                  ic = "⚪️" 
                result += f'{ic} {arr["text"]}\n'
             result += "\n/help /servers /s_"+_servname
             return result

       elif _ns=='SYS':
           _url = url.replace('/products/','/status-journal/10')
           if cmd.split("_")[2]=='AlertsView':
            _url = url.replace('/products/','/custom-task/user/run&class=apptools.MVK.utl&met=GetMetrixOneServer&par=all')
            
           err, resp = get_open(url=_url,timeout=TIMEOUT)
           #print('---=-',_url, err,type(resp), resp)
           result +=f'Статус:<b>{resp["status"]}</b>\n'
           if resp.get("array",''):
            for arr in resp["array"]:
                ic = arr['icon'] 
                if ic=='y':
                  ic = "🟡"
                elif ic=='r':
                  ic = "🔴"
                elif ic=='g':
                  ic = "⚪️" 
                result += f'{ic} {arr["text"]}\n'
            result += "\n/help /servers /s_"+_servname
            #print('---===-',result)
           return result
       _url = url.replace('/products/','/productslist/')+_ns
       err, resp = get_open(url=_url,timeout=TIMEOUT)
       result +=f'Сервер: <b>{resp["server"]}</b> Область: <b>{_ns}</b>\n'
       #print(err, resp)
       for ns in resp["ns"]:
          if ns['namespace']==_ns:
             for err in ns["errors"]:
                result += f"📆 <b>{err['TimeLogged']}</b> {err['Text'][0:200].replace('<','(').replace('>',')')}\n"
       result += "\n/help /servers /s_"+_servname
    else:
      err, resp = get_open(url=f'{url}1',timeout=TIMEOUT)
      #print(err, resp)
      if err.find("_OK")!=-1: # Если в статусе найден _OK в какой то там позиции
          count = len(resp["ns"]) if "ns" in resp else 0
          prod=""
          if count:
            for ns in resp["ns"]:
              icon = "🔴" if ns['counterrors'] else "🟡"
              _ns = ns['namespace'] 
              if _ns.find('-'):
                 _ns = _ns.replace("-","v")
              prod += f"{icon} /s_{cmd.split('_')[0]}_{_ns} Errors:{ns['counterrors']} \n"
          msg= f'<b>{resp["server"]}</b>, Продукций: {count}, Ошибок за 3 дня\n🟢 /s_{_servname}_SYS\n🔵 /s_{_servname}_SYS_AlertsView\n{prod}'
      else:
          msg = "🔴 Нет доступа"
          #
      cc = get_custom_commands(_servname,'list') # прикладные команды берем из .env
      result += f'{msg}{cc}{BR} /help'
    return result

def get_custom_commands(servname: str, mode: str) -> None:
    #url = os.getenv('CC_SERPAN_TEMP_VIEW') # CC_SERPAN_TEMP_VIEW = http://m   
    result=''
    #for key in os.environ:
    for key in plugins_iris:
      if f"CC_{servname}_" in key:
        #print(key, '=>', os.environ[key])
        if mode=="list":
          result += f'🟤 /s_{servname}_CC_{key.split("_")[2]}\n' #👉
        else:
          #result += key.split("URL_")[1]
          #Загрузить из сервиса результат
          #_u = os.environ[key]
          _u = plugins_iris[key]
          #print('-url-',_u )
          err, resp = get_open(url=_u,timeout=TIMEOUT) # 0 - Только статус
          #print(err, resp)
    return result