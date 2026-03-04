# Name Plugin: DATA
# https://catalog.eaist.mos.ru/catalog
# https://data.mos.ru/developers/documentation
# https://dadata.ru/api/find-party/
# https://dadata.ru/api/find-address/

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent.parent  # Поднимаемся на 3 уровня вверх
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from dadata import Dadata
from dtb.settings import get_plugins_for_roles

plugin_data = get_plugins_for_roles('').get('DATA')
token = plugin_data.get('dadata_token','')
secret = plugin_data.get('dadata_secret','')


def get_adress_fias(fias):
    dadata = Dadata(token,secret)
    result = dadata.find_by_id("address", fias)
    print(result)
    if result:
        val = result[0]['value']
    else:
        val = ''
    return val, result

def get_phone(txt):
    try:
        dadata = Dadata(token, secret)
        result = dadata.clean("phone", txt)
        if result:
            val = result['phone']
        else:
            val = ''
        return val, result
    except Exception as e:
        print(e)
        return '', ''       

def get_org(txt):
    try:
        dadata = Dadata(token)
        result = dadata.suggest(name="party", query=txt, count=1)
        
        if result:
            val = "" #result['value']
        else:
            val = ''
        return val, result
    except Exception as e:
        print(e)
        return '', ''       



if __name__ == "__main__":
   
    txt = "ооо Ромашка"
    # val, result = get_phone(txt)
    val, result = get_org(txt)

    
    print(val, result)
    #get_adress_fias(token,secret,"343434343434")
    pass