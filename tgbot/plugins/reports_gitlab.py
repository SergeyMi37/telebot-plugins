# Plugin for reporting from issue Gitlab ----- нестандарный
# Name Plugin: GITLAB

#from datetime import timedelta

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
from tgbot.handlers.utils.decorators import admin_only, send_typing_action
from tgbot.handlers.utils.date_utils import tz_to_moscow
from users.models import User

import os
from pathlib import Path
from typing import Any
#import datetime
from datetime import datetime, timedelta
from tgbot.handlers.utils.decorators import check_groupe_user
import requests
import json
from openpyxl import Workbook
from dtb.settings import get_plugins
from dtb.settings import logger

# Добавить проверку на роль 
plugins_gitlab = get_plugins('').get('GITLAB')
#logger.info('--- plugin GITLAB: '+str(plugins_gitlab))

if plugins_gitlab:
  ACCESS_TOKEN = plugins_gitlab.get('ACCESS_TOKEN')
  GRAPHQL_URL = plugins_gitlab.get('GRAPHQL_URL')
  GITLAB_URL = plugins_gitlab.get('GITLAB_URL')
  GITLAB_LABELS = plugins_gitlab.get('GITLAB_LABELS')
  PROJ_EN = plugins_gitlab.get('PROJ_EN','')
  PROJ_RU = plugins_gitlab.get('PROJ_RU','')
else:
  ACCESS_TOKEN = ''
  GRAPHQL_URL = ''
  GITLAB_URL = ''
  GITLAB_LABELS = ''
  PROJ_EN = ''
  PROJ_RU = ''

@check_groupe_user
def command_yesterday(update: Update, context: CallbackContext) -> None:
  _fromDate = datetime.now() + timedelta(days=-1)
  fromDate=_fromDate.date()
  command_daily(update, context, reportDate = fromDate )

@check_groupe_user
def command_daily(update: Update, context: CallbackContext, reportDate = '' ) -> None:
    u = User.get_user(update, context)
    if not u.is_admin:
        update.message.reply_text(only_for_admins)
        return
    if reportDate:
      fromDate = reportDate
    else:
       fromDate = datetime.today().date()
    labels = GITLAB_LABELS
    put_report(update=update, fromDate=fromDate,label=labels)

def lab_replay(lb: str, direct: str):
  if not PROJ_RU:
    return lb
  _i=0
  if direct=='ru_en':
    for _ru in PROJ_RU.split(","):
      lb=lb.replace(_ru, PROJ_EN.split(",")[_i])
      _i += 1
    lb=lb.replace("Табель","tabel").replace(",","_")
  else:
    for _en in PROJ_EN.split(","):
      lb=lb.replace(_en, PROJ_RU.split(",")[_i])
      _i += 1
    lb=lb.replace("tabel","Табель").replace("_",",")
  return lb
  
def get_lab(cmdmess: str):
  if not PROJ_EN:
    return 'CODE_GITLAB_PLUGIN_NOT'
  lab = "Рейтинг" 
  _i=0
  for _en in PROJ_EN.split(","):
    if f'_{_en}' in cmdmess:
      lab =  PROJ_RU.split(",")[_i]
      break
    _i += 1
  return lab

@check_groupe_user
def command_daily_rating_noname(update: Update, context: CallbackContext,lab = "") -> None:
    u = User.get_user(update, context)
    if not u.is_admin:
        update.message.reply_text(only_for_admins)
        return
    fromDate=datetime.today().date()
    lab = get_lab(update.message.text)
    labels = GITLAB_LABELS + "," + lab
    put_report(update=update, fromDate=fromDate,label=labels,mode="noname")

@check_groupe_user
def command_daily_rating(update: Update, context: CallbackContext,lab = "") -> None:
    u = User.get_user(update, context)
    if not u.is_admin:
        update.message.reply_text(only_for_admins)
        return
    
    fromDate = datetime.today().date() if 'daily_' in update.message.text else (datetime.now() + timedelta(days=-1)).date()
    lab = get_lab(update.message.text)
    labels = GITLAB_LABELS + ","+lab
    put_report(update=update, fromDate=fromDate,label=labels)
    
@check_groupe_user
def command_weekly_rating(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    fromDate = (datetime.now() + timedelta(days=-7)).date()
    toDate = datetime.today().date()
    if not u.is_admin:
        update.message.reply_text(only_for_admins)
        return
    lab = get_lab(update.message.text)
    labels = GITLAB_LABELS + ","+lab
    put_report(update=update,fromDate=fromDate,toDate=toDate,label=labels,mode='weekly')

def get_issues(url: str,
                    labels: str = 'Табель',
                    scope: str = 'all',
                    state: str = 'opened',
                    due_date: str = 'month') -> tuple[int, Any]:
  ret=""
  errno = "code.CODE_GITLAB_GET_ISSUE_OK"
  _url='{0:s}?labels={1:s}&scope={2:s}&state={3:s}&due_date={4:s}&per_page=100'.format(GITLAB_URL, labels, scope, state, due_date)
  try:
    headers = {
        #'Authorization': 'Bearer {0:s}'.format(ACCESS_TOKEN),
        'PRIVATE-TOKEN': ACCESS_TOKEN,
        'Accept': 'application/json;odata=verbose'
        }
    #print('---',_url,headers)
    responce = requests.get(_url,verify=False,headers=headers)
    response_list=responce.json()
    for it in response_list:
        print(it["iid"],it["title"],it['updated_at'])
        ret=ret +f"/n{it['iid']} {it['title']} {it['updated_at']}"

  except Exception as e:
    errno = "code.CODE_GITLAB_GET_ISSUE_FAIL"
    ret=e.args.__repr__()
    answer = {
      "errno": errno,
      'err_message': '{0}:{1}'.format("code.get_message(errno)", e.args.__repr__())
    }
  return errno, ret

def get_open_issues(url: str,
                    labels: str = 'Табель',
                    scope: str = 'all',
                    state: str = 'opened',
                    due_date: str = 'month') -> tuple[int, Any]:
  ret=""
  errno = "code.CODE_GITLAB_GET_ISSUE_OK"
  #_url='{0:s}?labels={1:s}&scope={2:s}&state={3:s}&due_date={4:s}&per_page=100'.format(GITLAB_URL, labels, scope, state, due_date)
  _url='{0:s}?labels={1:s}&scope={2:s}&per_page=100'.format(GITLAB_URL, labels, scope, state, due_date)
  headers = {
        #'Authorization': 'Bearer {0:s}'.format(ACCESS_TOKEN),
        'PRIVATE-TOKEN': ACCESS_TOKEN,
        'Accept': 'application/json;odata=verbose'
        }
  #print('---',_url,headers)
  try:
      response = requests.get(_url,verify=False,headers=headers)
      if response.status_code == 200:
        answer = json.loads(response.text)
        return "code.CODE_GITLAB_GET_ISSUE_OK", answer
      elif response.status_code == 404:
        return "code.CODE_GITLAB_ISSUE_EMPTY", None
      else:
        errno = "code.CODE_GITLAB_GET_ISSUE_FAIL"
        answer = {
          "errno": errno,
          'err_message': '{0:s}:{1:s}'.format(errno, response.text)
        }
        raise Exception(answer.get('err_message'))
  except Exception as e:
    errno = "code.CODE_GITLAB_GET_ISSUE_FAIL"
    answer = {
      "errno": errno,
      'err_message': '{0}:{1}'.format(errno, e.args.__repr__())
    }
    return errno, answer

def post_issue(url: str = GRAPHQL_URL, number_issue: int = None) -> tuple[int, Any]:
  headers = {
    'Authorization': 'Bearer {0:s}'.format(ACCESS_TOKEN),
    'Content-Type': 'application/json'
  }
  bodies = {
    "operationName": "issueTimeTrackingReport",
    "variables": {
      "id": "gid://gitlab/Issue/{0}".format(number_issue)
    },
    "query": "query issueTimeTrackingReport($id: IssueID\u0021) {\n  issuable: issue(id: $id) {\n    id\n    title\n    timelogs (first: 100) {\n      nodes {\n        ...TimelogFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment TimelogFragment on Timelog {\n  __typename\n  id\n  timeSpent\n  user {\n    id\n    name\n    __typename\n  }\n  spentAt\n  note {\n    id\n    body\n    __typename\n  }\n  summary\n  userPermissions {\n    adminTimelog\n    __typename\n  }\n}"
  }
  try:
      response = requests.post(url=url, verify=False, headers=headers, json=bodies)
      if response.status_code == 200:
        answer = json.loads(response.text)
        return "code.CODE_GITLAB_GET_ISSUE_TRACKING_OK", answer
      elif response.status_code == 404:
        return "code.CODE_GITLAB_ISSUE_TRACKING_EMPTY", None
      else:
        errno = "code.CODE_GITLAB_GET_ISSUE_TRACKING_FAIL"
        answer = {
          "errno": errno,
          'err_message': errno
        }
        raise Exception(answer.get('err_message'))
  except Exception as e:
    errno = "code.CODE_GITLAB_GET_ISSUE_TRACKING_FAIL"
    answer = {
      "errno": errno,
      'err_message': '{0}:{1}'.format(errno, e.args.__repr__())
    }
    return errno, answer

def get_issues_id(url: str = GITLAB_URL, labels: str = GITLAB_LABELS, scope: str = 'all', ) -> tuple[int, Any]:
  '''
  Функция REST API Gitlab для получения открытых issue
  :param url: url gitlab ресурса
  :param labels: Метки которые позволяют найти нужный контекст
  :param scope: область issue по умолчанию берутся все, а не текущего пользователя
  :return: list[id]
  '''
  errno, answer = get_open_issues(url=url, labels=labels, scope=scope)
  if errno == "code.CODE_GITLAB_GET_ISSUE_OK":
    issues_id = []
    for issue in answer:
      issues_id.append(int(issue.get('id')))
      print("=",issue.get('id'),issue.get('title'))
    return errno, issues_id
  else:
    return errno, answer

def get_report_issue(id_issue: int = None, fromDate: datetime="", toDate: datetime="", mode: str='name') -> tuple[int, Any, str]:
  '''
  Получение отчета прикрепленного к конкретному issue
  :param id_issue: id обсуждения
  :return: список содержащий информацию для отчета по обсуждению
  '''
  errno, answer = post_issue(number_issue=id_issue)
  #if id_issue==721:print("===",id_issue,answer)
  answer_list = []
  summ=""
  week={}
  answer_item = dict()
  if errno == "code.CODE_GITLAB_GET_ISSUE_TRACKING_OK":
    if answer.get('data') is not None:
      if answer.get('data').get('issuable') is not None:
        #
        #answer_item['id_issue'] = validate_int_is_none(get_last_for_split(answer.get('data').get('issuable').get('id')))
        answer_item['title'] = answer.get('data').get('issuable').get('title')
        for item in answer.get('data').get('issuable').get('timelogs').get('nodes'):
          answer_item['name'] = item.get('user').get('name')
          summary=str(item.get('summary'))
          answer_item['summary'] = summary
          answer_item['note'] = item.get('note')
          _spentAt=item.get('spentAt')
          answer_item['spent_at'] = tz_to_moscow(_spentAt)
          #if id_issue==721:            print("---",answer_item['name'],answer_item['spent_at'],str(item.get('summary')))
          if answer_item['spent_at']>=fromDate and (answer_item['spent_at']<=toDate):
            #if id_issue==721:              print("------",answer_item['spent_at'],str(item.get('summary')))
            userfio=''
            if mode == 'weekly':
              #print('---',summary)
              if "$" in summary and (summary.split("$")[0] !='') :
                #week += summary.split("$")[0] + CRLF
                week[f'{summary.split("$")[0]}']={}
            elif mode != "noname":
                userfio=f'{answer_item["name"].split(" ")[0]} {answer_item["spent_at"].strftime("%Y-%m-%d")} {item.get("spentAt")} {CRLF}'
            
            summ += f"{userfio} {summary.replace('$','.') }{CRLF+CRLF}"
          answer_list.append(answer_item)
        return errno, answer_list, summ, week
      else:
        errno = "code.CODE_GITLAB_ISSUE_TRACKING_EMPTY"
        answer = {
          "errno": errno,
          'err_message': (errno)
        }
    else:
      errno = "code.CODE_GITLAB_BAD_REQUEST"
      err_message = answer.get('errors')[0].get('message')
      answer = {
        'errno': errno,
        'err_message': f'{(errno)}:{err_message}'
      }
    return errno, answer, summ, week
  else:
    return errno, answer, summ, week

def get_report(label: str = "Табель", fromDate: datetime="", toDate: datetime="", mode: str='name', pref: str=''):
    if toDate=='':
       toDate=fromDate
    if toDate==fromDate:
      _date=f'за {fromDate}'
    else:
      _date=f'с {fromDate} по {toDate}'

    #prefix = f"<pre>/reports date:{fromDate}:{toDate} mode:{mode} labels:{label}</pre>" if pref=='' else pref
    fd=str(fromDate).replace("-","")
    td=str(toDate).replace("-","")
    #lb=label.replace("Рейтинг","rating").replace("ВПР","vpr").replace("Табель","tabel").replace(",","_")
    lb = lab_replay(label,"ru_en")
    #print("---====-ru_en-",label,lb)
    prefix = f"/reports_date_{fd}_{td}_mode_{mode}_labels_{lb}" if pref=='' else pref
    
    errno, answer = get_issues_id(GITLAB_URL,label)
    #print('---',errno, answer)
    summ=f"{label}{CRLF}Выполненные мероприятия {_date}{CRLF+CRLF}"
    sum=summ
    week={}
    if errno == "code.CODE_GITLAB_GET_ISSUE_OK":
        for item in answer:
            errno, answer, _summ, _week = get_report_issue(id_issue=item, fromDate=fromDate, toDate=toDate, mode=mode)
            summ=summ+_summ
            week= {**week, **_week}
        if summ==sum:
           summ=summ+' не найдено'
        summ += CRLF+'🔸/help'
        return summ, prefix, week #[:4090]
    else:
       return errno, prefix, week

def put_report(update: Update, label: str = "", fromDate: datetime="", toDate: datetime="", mode: str='name'):

    txt, pref, week = get_report(fromDate=fromDate,toDate=toDate,label=label,mode=mode)
    upms = get_tele_command(update)
    telecmd = upms.text
    CONST = 4090
    ot=0
    do=CONST
    
    if mode == 'weekly':
      text = pref +CRLF+ "<b>Недельная сводка</b>" + CRLF + CRLF
      for key in week:
         text += key + CRLF + CRLF
    else:
      text = pref +CRLF+ txt 

    media_dir = Path(__file__).resolve().parent.parent.parent.parent.joinpath('downloads')
    if not os.path.exists(media_dir):
      os.mkdir(media_dir)
    # Вывод в файл XLSX -----------------------------------------
    if mode=='xlsx':
      wb = Workbook() # creates a workbook object.
      ws = wb.active # creates a worksheet object.
      #_out=[[f"{pref}"],["Дата","ФИО", "Дата UTC", "Мероприятия"]]
      outlist = text.split(CRLF)
      #ws.append([f"{pref}"])
      ws.append([f"{outlist[2]}"])
      
      ws.append(["Дата","ФИО", "Дата UTC", "Мероприятия"])
      head = ""
      for row in outlist[3:-1]:
        if row !='':
          if head=="":
             head=row
             continue
          else:
            ws.append([f'{head.split(" ")[1]}',f'{head.split(" ")[0]}',f'{head.split(" ")[2]}',row])
            head=""

      ws.column_dimensions.__getitem__("A").width = "15"
      ws.column_dimensions.__getitem__("B").width = "20"
      ws.column_dimensions.__getitem__("C").width = "20"
      ws.column_dimensions.__getitem__("D").width = "90"
      ws.freeze_panes="B3"
      _file = os.path.join(media_dir, f'{telecmd[1:-1]}_{upms.chat.id}.xlsx')
      wb.save(_file) # save to excel file.
      upms.reply_document(open(_file, 'rb'))
    
    # Вывод в текстовый файл -----------------------------------------
    elif mode=='txt':
      lines = text.split(CRLF)
      _file = os.path.join(media_dir, f'{telecmd[1:-1]}_{upms.chat.id}.txt')
      with open(_file, "w") as file:
        for  line in lines:
          if line !='':
            file.write(line + '\n')
      upms.reply_document(open(_file, 'rb'))
      #for row in txt.split(CRLF):
      #  print(row)

    # вывод в цикле текстом  -----------------------------------------
    else:
      while True:
        upms.reply_text(
          text = text[ot:do],
          parse_mode=ParseMode.HTML,
          disable_web_page_preview=True,
          )
        ot=ot+CONST
        do=do+CONST
        if text[ot:do]=='':
          break
    
