"""
'document': {
    'file_name': 'preds (4).csv', 'mime_type': 'text/csv', 
    'file_id': 'BQACAgIAAxkBAAIJ8F-QAVpXcgUgCUtr2OAHN-OC_2bmAAJwBwAC53CASIpMq-3ePqBXGwQ', 
    'file_unique_id': 'AgADcAcAAudwgEg', 'file_size': 28775
}
'photo': [
    {'file_id': 'AgACAgIAAxkBAAIJ-F-QCOHZUv6Kmf_Z3eVSmByix_IwAAOvMRvncIBIYJQP2Js-sAWGaBiVLgADAQADAgADbQADjpMFAAEbBA', 'file_unique_id': 'AQADhmgYlS4AA46TBQAB', 'file_size': 13256, 'width': 148, 'height': 320}, 
    {'file_id': 'AgACAgIAAxkBAAIJ-F-QCOHZUv6Kmf_Z3eVSmByix_IwAAOvMRvncIBIYJQP2Js-sAWGaBiVLgADAQADAgADeAADkJMFAAEbBA', 'file_unique_id': 'AQADhmgYlS4AA5CTBQAB', 'file_size': 50857, 'width': 369, 'height': 800}, 
    {'file_id': 'AgACAgIAAxkBAAIJ-F-QCOHZUv6Kmf_Z3eVSmByix_IwAAOvMRvncIBIYJQP2Js-sAWGaBiVLgADAQADAgADeQADj5MFAAEbBA', 'file_unique_id': 'AQADhmgYlS4AA4-TBQAB', 'file_size': 76018, 'width': 591, 'height': 1280}
]
'video_note': {
    'duration': 2, 'length': 300, 
    'thumb': {'file_id': 'AAMCAgADGQEAAgn_XaLgADAQAHbQADQCYAAhsE', 'file_unique_id': 'AQADWoxsmi4AA0AmAAI', 'file_size': 11684, 'width': 300, 'height': 300}, 
    'file_id': 'DQACAgIAAxkBAAIJCASO6_6Hj8qY3PGwQ', 'file_unique_id': 'AgADeQcAAudwgEg', 'file_size': 102840
}
'voice': {
    'duration': 1, 'mime_type': 'audio/ogg', 
    'file_id': 'AwACAgIAAxkBAAIKAAFfkAu_8Ntpv8n9WWHETutijg20nAACegcAAudwgEi8N3Tjeom0IxsE', 
    'file_unique_id': 'AgADegcAAudwgEg', 'file_size': 4391
}
'sticker': {
    'width': 512, 'height': 512, 'emoji': '🤔', 'set_name': 's121356145_282028_by_stickerfacebot', 'is_animated': False, 
    'thumb': {
        'file_id': 'AAMCAgADGQEAAgJUX5A5icQq_0qkwXnihR_MJuCKSRAAAmQAA3G_Owev57igO1Oj4itVTZguAAMBAAdtAAObPwACGwQ', 'file_unique_id': 'AQADK1VNmC4AA5s_AAI', 'file_size': 14242, 'width': 320, 'height': 320
    }, 
    'file_id': 'CAACAgIAAxkBAAICVF-QOYnEKv9KpMF54oUfzCbgikkQAAJkAANxvzsHr-e4oDtTo-IbBA', 'file_unique_id': 'AgADZAADcb87Bw', 'file_size': 25182
}
'video': {
    'duration': 14, 'width': 480, 'height': 854, 'mime_type': 'video/mp4', 
    'thumb': {'file_id': 'AAMCAgADGQEAAgoIX5BAQy-AfwmWLgADAQAHbQADJhAAAhsE', 'file_unique_id': 'AQAD5H8Jli4AAyYQAAI', 'file_size': 9724, 'width': 180, 'height': 320}, 
    'file_id': 'BAACAgIIAAKaCAACCcGASLV2hk3MavHGGwQ', 
    'file_unique_id': 'AgADmggAAgnBgEg', 'file_size': 1260506}, 'caption': '50603'
}
"""
from typing import Dict

import telegram
from telegram import Update
from telegram.ext import CallbackContext
import os
from pathlib import Path
from dtb.settings import settings
 
from users.models import User

ALL_TG_FILE_TYPES = ["document", "video_note", "voice", "sticker", "audio", "video", "animation", "photo"]

down = 'downloads' if not settings.get("DOWNLOADS_PATH") else settings.get("DOWNLOADS_PATH")
media_dir = Path(__file__).resolve().parent.parent.parent.parent.joinpath(down)
if not os.path.exists(media_dir):
    os.mkdir(media_dir)

def _get_file_id(m: Dict) -> str:
    """ extract file_id from message (and file type?) """

    for doc_type in ALL_TG_FILE_TYPES:
        if doc_type in m and doc_type != "photo":
            return m[doc_type]["file_id"]

    if "photo" in m:
        best_photo = m["photo"][-1]
        return best_photo["file_id"]


def show_file_id(update: Update, context: CallbackContext) -> None:
    """ Returns file_id of the attached file/media """
    u = User.get_user(update, context)

    if u.is_admin:
        update_json = update.to_dict()
        file_id = _get_file_id(update_json["message"])
        message_id = update_json["message"]["message_id"]
        update.message.reply_text(
            text=f"`{file_id}`",
            parse_mode=telegram.ParseMode.HTML,
            reply_to_message_id=message_id
        )

def save_file_id(update: Update, context: CallbackContext) -> None:
    """ Returns file_id of the attached file/media and save"""
    u = User.get_user(update, context)

    if u.is_admin:
        update_json = update.to_dict()
        #print(update_json)
        file_id = _get_file_id(update_json["message"])
        #message_id = update_json["message"]["message_id"]
        cid = str(update_json["message"]["chat"]['id'])
        file_name = update_json["message"]["document"]['file_name']
        bot = context.bot
        try:
            file = bot.get_file(file_id)
            #print(file,file_id,message_id)
            _dir = os.path.join(media_dir, cid)
            if not os.path.exists(_dir):
                os.mkdir(_dir)
            _file = os.path.join(_dir, f'{file_name}')
            file.download(custom_path = _file)
            update.message.reply_text(f"Файл успешно сохранён.{_file}")
        except Exception as e:
            update.message.reply_text(f"Произошла ошибка при скачивании файла: {e}")

        # update_json = update.to_dict()
        # #print(update_json)
        # file_id = _get_file_id(update_json["message"])
        # #message_id = update_json["message"]["message_id"]
        # cid = str(update_json["message"]["chat"]['id'])
        # file_name = update_json["message"]["document"]['file_name']
        # bot = context.bot
        # try:
        #     file = bot.get_file(file_id)
        #     #print(file,file_id,message_id)
        #     _dir = os.path.join(media_dir, cid)
        #     if not os.path.exists(_dir):
        #         os.mkdir(_dir)
        #     _file = os.path.join(_dir, f'{file_name}')
