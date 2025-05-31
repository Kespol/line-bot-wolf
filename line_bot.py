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
        "chock_image": "https://drive.google.com/uc?export=view&id=1KEX8y7gU-w5vdfXn5sG830RUAFSXISbL"
    },
    "AXM馬亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "APG菲亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "APG普航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CHH海南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CSS順風": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "JAL真航空": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 TTW代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "EOK可依": {
        "towbar": "EOK",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁飲水合約內 熊航代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "ESR易斯達": {
        "towbar": "台亞",
        "headset": "需要",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "熊航代理 易斯達專用拖桿在A4 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "FDX聯邦": {
        "towbar": "FDX",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "棚廠維修支援推機要簽單 人工引導要簽單 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "AHK華民貨機": {
        "towbar": "AHK或CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "A330不用綁帶 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "AMU澳門": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過境移機要簽單 過夜同機號第三次移機要簽單 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1lzSqeQ1byWegvisZURZPMO7xKRRvUy2_"
    },
    "CSC四川": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CSH上海": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CSN南方": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CSZ深圳": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CCA國航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CKK中貨航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CDG山東": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CYZ中郵航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "HVN越南": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1lzSqeQ1byWegvisZURZPMO7xKRRvUy2_"
    },
    "JSA捷星": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=19FfKLQGQka8lko2t-W1lUSlyOHT-gc1i"
    },
    "MAS馬航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1uCmxwhwiDtRFSvLvwUWRiHtsnyN68FWi"
    },
    "JTA越洋": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不用開關門 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "GTI亞特拉斯": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "APJ樂桃": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "可無拖桿車及人員運送車SSU 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "MXD峇迪": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "MMA緬甸": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "拖桿在A3 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "TLM泰獅": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1lzSqeQ1byWegvisZURZPMO7xKRRvUy2_"
    },
    "KAL韓航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "飲水合約內 A380要專用拖桿 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "JJA濟州": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CAL中華": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機要電源車 擦玻璃free 扶梯車要寫時間 A坪和B坪要橋氣電 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "MDA華信": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "擦玻璃free 扶梯車要寫時間 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CLX盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Zk1UfT-0IvqBkc3K9JADXfBQOwCFgUIR"
    },
    "ICV盧森堡": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "748清廁不加藥水 組員車合約內 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Zk1UfT-0IvqBkc3K9JADXfBQOwCFgUIR"
    },
    "CES東方": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CEB宿霧": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "旅客扶梯收費 可用無拖桿車 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1lzSqeQ1byWegvisZURZPMO7xKRRvUy2_"
    },
    "CXA廈門": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "CPA國泰客貨": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "on call",
        "water_service": "on call",
        "others": "各時段各項裝備分開單獨開白單 客機擦玻璃free 貨機擦玻璃要簽單 水系消毒要註明3次 當班加水清廁要簽單 過夜消毒要簽白單 過夜起站加水不簽 組員車free 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "DAL達美": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "過夜同機號移機第三次簽單 過境移機要簽單 過境BCU-過夜on call簽單 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1yKqMMLshdF2Sads4QxhcWJRNPelHrWGF"  # 更改輪檔圖片
    },
    "BTK巴澤": {
        "towbar": "TLM 天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "夜間2300~0700 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "BAV越竹": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "KLM荷航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1BTXGaagiOIe3pL8EgaY41N_Zf1bivd7T"
    },
    "HKE香港快運": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "HGB大灣區": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "TIAS代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "HKC香港貨運": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "不綁帶 含一次移機 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "JAL日航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不可用無拖桿車 BCU FREE 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "JAL日航貨": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水free 不綁帶 BCU FREE 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "JJP日捷": {
        "towbar": "CAL TTW",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1E_-I2LBFIl19tcf-S_ZkOARZEn2i_tYa"
    },
    "XAX全亞": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1E_-I2LBFIl19tcf-S_ZkOARZEn2i_tYa"
    },
    "VJC越捷": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "TTW代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1KdLxut3n9nxcRnLj5OVV9Yv-09gr5vRU"
    },
    "VAG越旅": {
        "towbar": "天際 台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1lzSqeQ1byWegvisZURZPMO7xKRRvUy2_"
    },
    "YZR-757揚子江": {
        "towbar": "無拖桿車",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "清廁飲水合約內 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "YZR-737揚子江": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "UAE阿酋": {
        "towbar": "CPA",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "貨機777不綁帶2300~0700 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1rI55bor5G_5Nqz5x1GoyMRd7QQ8JMeiq"
    },
    "UAL聯合": {
        "towbar": "UAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 支援後推要簽單 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "THY土航": {
        "towbar": "CAL",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "清廁不加藥水 飛機輪檔要等修護或是loading說好才能放 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "THA泰航": {
        "towbar": "TIAS",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1uCmxwhwiDtRFSvLvwUWRiHtsnyN68FWi"
    },
    "QFA澳洲": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "TVJ泰越捷": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "L3靠扶梯車加油用不簽單 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1KdLxut3n9nxcRnLj5OVV9Yv-09gr5vRU"
    },
    "TTW台虎": {
        "towbar": "CAL TTW",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "A坪和B坪要橋氣電 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "TWB德威": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1X62JNOchYwc9_37Et9pECzNHa8EhSO69"
    },
    "SIA新加坡貨機": {
        "towbar": "TIAS",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不綁帶 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "RBA汶萊": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "不可用無拖桿車 TIAS代理 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1uCmxwhwiDtRFSvLvwUWRiHtsnyN68FWi"
    },
    "RYL菲皇": {
        "towbar": "天際台亞",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "不需",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "PAC保羅": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "雙交管 其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=19FfKLQGQka8lko2t-W1lUSlyOHT-gc1i"
    },
    "捷星太平洋": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1dqykhTR1P0XWD1OMGuraNtJKD6IBbAKN"
    },
    "PAL菲航": {
        "towbar": "CAL",
        "headset": "需要",
        "bypass_pin": "需要",
        "gear_pin": "需要",
        "toilet_service": "需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
    },
    "PRI私人": {
        "towbar": "無",
        "headset": "不需",
        "bypass_pin": "不需",
        "gear_pin": "不需",
        "toilet_service": "不需要",
        "water_service": "不需要",
        "others": "其餘on call",
        "chock_image": "https://drive.google.com/uc?export=view&id=1Xd7sH3aAPwYlVqb2xWoAx1KJaHlegfpA"
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
        reply_text += "華航代理的787系列：專用拖桿在A9\n"
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