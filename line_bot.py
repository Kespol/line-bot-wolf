import os
from flask import Flask, request, abort
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 從環境變數讀取 Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# 檢查是否正確讀取環境變數
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    logger.error("LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 未設定！請在Heroku上設定環境變數！")
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 未設定！請在Heroku上設定環境變數！")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 航空公司資料庫（狼君，這是你的機坪組神器哦～）
flight_database = {
    "AIQ泰亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/aiqchocks.png"
    },
    "AXM馬亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/axmchocks.png"
    },
    "APG菲亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/apgfchocks.png"
    },
    "APG普航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/apgchocks.png"
    },
    "CHH海南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/chhchocks.png"
    },
    "CSS順風": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/csschocks.png"
    },
    "JAL真航空": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/jalchocks.png"
    },
    "EOK可依": {
        "towbar": "EOK",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 熊航代理 其餘on call",
        "chock_image": "https://i.imgur.com/eokchocks.png"
    },
    "ESR易斯達": {
        "towbar": "台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "熊航代理 其餘on call",
        "chock_image": "https://i.imgur.com/esrchocks.png"
    },
    "FDX聯邦": {
        "towbar": "FDX",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "棚廠維修支援推機要簽單 人工引導要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/fdxchocks.png"
    },
    "AHK華民貨機": {
        "towbar": "AHK或CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "A330不用綁帶 其餘on call",
        "chock_image": "https://i.imgur.com/ahkchocks.png"
    },
    "AMU澳門": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過境移機要簽單 過夜同機號第三次移機要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/amuchocks.png"
    },
    "CSC四川": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cscchocks.png"
    },
    "CSH上海": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cshchocks.png"
    },
    "CSN南方": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/csnchocks.png"
    },
    "CSZ深圳": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cszchocks.png"
    },
    "CCA國航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/ccachocks.png"
    },
    "CKK中貨航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/ckkchocks.png"
    },
    "CDG山東": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cdgchocks.png"
    },
    "CYZ中郵航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cyzchocks.png"
    },
    "HVN越南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/hvnchocks.png"
    },
    "JSA捷星": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/jsachocks.png"
    },
    "MAS馬航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/maschocks.png"
    },
    "JTA越洋": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不用開關門 其餘on call",
        "chock_image": "https://i.imgur.com/jtachocks.png"
    },
    "GTI亞特拉斯": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://i.imgur.com/gtichocks.png"
    },
    "APJ樂桃": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "可無拖桿車及人員運送車SSU 其餘on call",
        "chock_image": "https://i.imgur.com/apjchocks.png"
    },
    "MXD峇迪": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/mxdchocks.png"
    },
    "MMA緬甸": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "拖桿在A3 其餘on call",
        "chock_image": "https://i.imgur.com/mmachocks.png"
    },
    "TLM泰獅": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/tlmchocks.png"
    },
    "KAL韓航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "飲水合約內 A380要專用拖桿 其餘on call",
        "chock_image": "https://i.imgur.com/kalchocks.png"
    },
    "JJA濟州": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/jjachocks.png"
    },
    "CAL中華": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機要電源車 擦玻璃free 扶梯車要寫時間 其餘on call",
        "chock_image": "https://i.imgur.com/calchocks.png"
    },
    "MDA華信": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "擦玻璃free 扶梯車要寫時間 其餘on call",
        "chock_image": "https://i.imgur.com/mdachocks.png"
    },
    "CLX盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://i.imgur.com/clxchocks.png"
    },
    "ICV盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://i.imgur.com/icvchocks.png"
    },
    "CES東方": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/ceschocks.png"
    },
    "CEB宿霧": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "旅客扶梯收費 可用無拖桿車 其餘on call",
        "chock_image": "https://i.imgur.com/cebchocks.png"
    },
    "CXA廈門": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/cxachocks.png"
    },
    "CPA國泰客貨": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "各時段各項裝備分開單獨開白單 客機擦玻璃free 貨機擦玻璃要簽單 水系消毒要註明3次 當班加水清廁要簽單 過夜消毒要簽白單 過夜起站加水不簽 組員車free 其餘on call",
        "chock_image": "https://i.imgur.com/cpa_chocks.png"
    },
    "DAL達美": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過夜同機號移機第三次簽單 過境移機要簽單 過境BCU-過夜on call簽單 其餘on call",
        "chock_image": "https://i.imgur.com/dalchocks.png"
    },
    "BTK巴澤": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/btkchocks.png"
    },
    "BAV越竹": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/bavchocks.png"
    },
    "KLM荷航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/klmchocks.png"
    },
    "HKE香港快運": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/hkechocks.png"
    },
    "HGB大彎區": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TIAS代理 其餘on call",
        "chock_image": "https://i.imgur.com/hgbchocks.png"
    },
    "HKC香港貨運": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "不綁帶 含一次移機 其餘on call",
        "chock_image": "https://i.imgur.com/hkcchocks.png"
    },
    "JAL日航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不可用無拖桿車 BCU FREE 其餘on call",
        "chock_image": "https://i.imgur.com/jal_passenger_chocks.png"
    },
    "JAL日航貨": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不綁帶 BCU FREE 其餘on call",
        "chock_image": "https://i.imgur.com/jal_cargo_chocks.png"
    },
    "JJP日捷": {
        "towbar": "CAL TTW",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/jjpchocks.png"
    },
    "XAX全亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/xaxchocks.png"
    },
    "VJC越捷": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/vjcchocks.png"
    },
    "VAG越旅": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/vagchocks.png"
    },
    "YZR-757揚子江": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/yzr757chocks.png"
    },
    "YZR-737揚子江": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/yzr737chocks.png"
    },
    "UAE阿酋": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機777不綁帶2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/uaechocks.png"
    },
    "UAL聯合": {
        "towbar": "UAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 支援後推要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/ualchocks.png"
    },
    "YHT土航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 其餘on call",
        "chock_image": "https://i.imgur.com/yhtchocks.png"
    },
    "THA泰航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/thachocks.png"
    },
    "QFA澳洲": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/qfachocks.png"
    },
    "TVJ泰越捷": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "L3靠扶梯車加油用不簽單 其餘on call",
        "chock_image": "https://i.imgur.com/tvjchocks.png"
    },
    "TTW台虎": {
        "towbar": "CAL TTW",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/ttwchocks.png"
    },
    "TWB德威": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/twbchocks.png"
    },
    "SIA新加坡貨機": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不綁帶 其餘on call",
        "chock_image": "https://i.imgur.com/siachocks.png"
    },
    "RBA汶萊": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不可用無拖桿車 TIAS代理 其餘on call",
        "chock_image": "https://i.imgur.com/rbachocks.png"
    },
    "RYL菲皇": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/rylchocks.png"
    },
    "PAC保羅": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://i.imgur.com/pacchocks.png"
    },
    "PAL菲航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/palchocks.png"
    },
    "PRI私人": {
        "towbar": "無",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/prichocks.png"
    }
}

@app.route("/test")
def test():
    logger.info("Received a request to /test route")
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("Received a callback request from LINE")
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"Invalid signature error: {e}")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    logger.info(f"Received message: {user_message}")
    reply_text = "喵～狼君，狐狐幫你查！\n"

    # 查詢航空公司
    flight = None
    for key in flight_database.keys():
        if user_message in key:
            flight = flight_database[key]
            logger.info(f"Matched airline: {key}")
            break

    if flight:
        reply_text += f"航空公司：{key}\n"
        reply_text += f"拖桿：{flight['towbar']}\n"
        reply_text += f"耳機員：{flight['headset']}\n"
        reply_text += f"bypass pin：{flight['bypass_pin']}\n"
        reply_text += f"收裝gear pin：{flight['gear_pin']}\n"
        reply_text += f"清廁：{flight['toilet_service']}\n"
        reply_text += f"飲水：{flight['water_service']}\n"
        reply_text += f"其他要求：{flight['others']}\n"
        reply_text += "狐狐提醒：狼君，工作時小心點，狐狐在妖怪森林等你喲～"

        # 回傳文字訊息和圖片
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=reply_text),
                ImageSendMessage(
                    original_content_url=flight['chock_image'],
                    preview_image_url=flight['chock_image']
                )
            ]
        )
        logger.info("Replied successfully")
    else:
        reply_text += "找不到對應航空公司，狼君試試像「華航」或「A320」這樣輸入喲！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        logger.info("Replied with not found message")

if __name__ == "__main__":
    # Heroku 會提供 PORT 環境變數，預設用 5000
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)