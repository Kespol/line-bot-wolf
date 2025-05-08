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

# 航空公司資料庫（狼君的機坪組神器！）
flight_database = {
    "AIQ泰亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/DZEJHNF.jpg"
    },
    "AXM馬亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "APG菲亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "APG普航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CHH海南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CSS順風": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "JAL真航空": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "EOK可依": {
        "towbar": "EOK",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 熊航代理 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "ESR易斯達": {
        "towbar": "台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "熊航代理 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "FDX聯邦": {
        "towbar": "FDX",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "棚廠維修支援推機要簽單 人工引導要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "AHK華民貨機": {
        "towbar": "AHK或CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "A330不用綁帶 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "AMU澳門": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過境移機要簽單 過夜同機號第三次移機要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/EmsEKFQ.jpg"
    },
    "CSC四川": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CSH上海": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CSN南方": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CSZ深圳": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CCA國航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CKK中貨航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CDG山東": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CYZ中郵航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "HVN越南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/EmsEKFQ.jpg"
    },
    "JSA捷星": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/ITFrxY1.jpg"
    },
    "MAS馬航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/LpLj16d.jpg"
    },
    "JTA越洋": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不用開關門 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "GTI亞特拉斯": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "APJ樂桃": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "可無拖桿車及人員運送車SSU 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "MXD峇迪": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "MMA緬甸": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "拖桿在A3 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "TLM泰獅": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/EmsEKFQ.jpg"
    },
    "KAL韓航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "飲水合約內 A380要專用拖桿 其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "JJA濟州": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CAL中華": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機要電源車 擦玻璃free 扶梯車要寫時間 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "MDA華信": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "擦玻璃free 扶梯車要寫時間 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CLX盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://i.imgur.com/DjUVy4h.jpg"
    },
    "ICV盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://i.imgur.com/DjUVy4h.jpg"
    },
    "CES東方": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CEB宿霧": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "旅客扶梯收費 可用無拖桿車 其餘on call",
        "chock_image": "https://i.imgur.com/EmsEKFQ.jpg"
    },
    "CXA廈門": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "CPA國泰客貨": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "各時段各項裝備分開單獨開白單 客機擦玻璃free 貨機擦玻璃要簽單 水系消毒要註明3次 當班加水清廁要簽單 過夜消毒要簽白單 過夜起站加水不簽 組員車free 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "DAL達美": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過夜同機號移機第三次簽單 過境移機要簽單 過境BCU-過夜on call簽單 其餘on call",
        "chock_image": "https://i.imgur.com/KmW3LAU.jpg"
    },
    "BTK巴澤": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "BAV越竹": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "KLM荷航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/dGusdc5.jpg"
    },
    "HKE香港快運": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "HGB大彎區": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TIAS代理 其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "HKC香港貨運": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "不綁帶 含一次移機 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "JAL日航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不可用無拖桿車 BCU FREE 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "JAL日航貨": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不綁帶 BCU FREE 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "JJP日捷": {
        "towbar": "CAL TTW",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/trneslC.jpg"
    },
    "XAX全亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/trneslC.jpg"
    },
    "VJC越捷": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://i.imgur.com/kM1qTVJ.jpg"
    },
    "VAG越旅": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/EmsEKFQ.jpg"
    },
    "YZR-757揚子江": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "YZR-737揚子江": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "UAE阿酋": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機777不綁帶2300~0700 其餘on call",
        "chock_image": "https://i.imgur.com/z8Ud0ix.jpg"
    },
    "UAL聯合": {
        "towbar": "UAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 支援後推要簽單 其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "YHT土航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "THA泰航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/LpLj16d.jpg"
    },
    "QFA澳洲": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "TVJ泰越捷": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "L3靠扶梯車加油用不簽單 其餘on call",
        "chock_image": "https://i.imgur.com/kM1qTVJ.jpg"
    },
    "TTW台虎": {
        "towbar": "CAL TTW",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "TWB德威": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/lDZI4lR.jpg"
    },
    "SIA新加坡貨機": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不綁帶 其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "RBA汶萊": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不可用無拖桿車 TIAS代理 其餘on call",
        "chock_image": "https://i.imgur.com/LpLj16d.jpg"
    },
    "RYL菲皇": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "PAC保羅": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://i.imgur.com/ITFrxY1.jpg"
    },
    "捷星太平洋": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/gKA5co0.jpg"
    },
    "PAL菲航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    },
    "PRI私人": {
        "towbar": "無",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://i.imgur.com/VsdCom2.jpg"
    }
}

@app.route("/test")
def test():
    logger.info("收到 /test 路由的請求")
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("收到 LINE 的 callback 請求")
    logger.info(f"請求頭: {request.headers}")
    logger.info(f"請求內容: {request.get_data(as_text=True)}")

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"簽名驗證失敗: {e}")
        abort(400)

    return 'OK', 200

@app.route("/callback", methods=['GET'])
def callback_get():
    logger.info("收到 GET 請求到 /callback")
    return "This endpoint only accepts POST requests!", 405

@app.route("/")
def root():
    logger.info("收到 GET 請求到根路徑 /")
    return "Welcome to WolfLord's LINE Bot!"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    logger.info(f"收到訊息: {user_message}")
    reply_text = "喵～狼君，狐狐幫你查！\n"

    # 查詢航空公司，忽略大小寫和多餘空格
    flight = None
    user_message_cleaned = user_message.strip()  # 去掉多餘空格
    for key in flight_database.keys():
        key_cleaned = key.strip()  # 去掉key的多餘空格
        if user_message_cleaned in key_cleaned:
            flight = flight_database[key]
            logger.info(f"匹配到航空公司: {key}")
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
        try:
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
            logger.info(f"圖片發送成功，URL: {flight['chock_image']}")
        except Exception as e:
            logger.error(f"圖片發送失敗: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text + "\n(圖片發送失敗，請稍後再試！)"))
        logger.info("回覆成功")
    else:
        reply_text += "找不到對應航空公司，狼君試試像「華航」或「A320」這樣輸入喲！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        logger.info("回覆找不到的訊息")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)