from dotenv import load_dotenv
load_dotenv()

import os
import json
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

print("=== ACCESS TOKEN ===", os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
print("=== SECRET ===", os.environ.get("LINE_CHANNEL_SECRET"))

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ====================== 航空公司資料庫 ======================
# 從 JSON 檔案載入航空公司資料
try:
    with open("flight_database.json", "r", encoding="utf-8") as f:
        flight_database = json.load(f)
    logger.info("成功從 flight_database.json 載入資料")
except FileNotFoundError:
    logger.error("找不到 flight_database.json，請確認檔案是否存在")
    flight_database = {}
except Exception as e:
    logger.error(f"載入 flight_database.json 失敗: {e}")
    flight_database = {}
# ====================== 路由 ======================
@app.route("/test")
def test():
    logger.info("收到 /test 路由的請求")
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("收到 LINE 的 callback 請求")
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

# ====================== 訊息處理 ======================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 把使用者輸入轉成小寫 + 去掉前後空格
    user_message = event.message.text.strip().lower()
    logger.info(f"收到訊息: {user_message}")

    flight = None
    matched_key = None

    for key, info in flight_database.items():
        # 把 key 轉小寫再比對
        if user_message in key.lower():
            flight = info
            matched_key = key
            break

        # 把 aliases 也轉小寫再比對
        if "aliases" in info:
            for alias in info.get("aliases", []):
                if user_message in alias.lower():
                    flight = info
                    matched_key = key
                    break

        if flight:
            break

    reply_text = "喵～狼君，狐狐幫你查！\n"

    if flight:
        reply_text += f"航空公司：{matched_key}\n"
        reply_text += f"拖桿：{flight['towbar']}\n"
        reply_text += f"耳機員：{flight['headset']}\n"
        reply_text += f"bypass pin：{flight['bypass_pin']}\n"
        reply_text += f"收裝gear pin：{flight['gear_pin']}\n"
        reply_text += f"清廁：{flight['toilet_service']}\n"
        reply_text += f"飲水：{flight['water_service']}\n"
        reply_text += f"其他要求：{flight['others']}\n"
        reply_text += "華航代理的787系列：專用拖桿在A9\n"
        reply_text += "狐狐提醒：工作時小心點～"

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
            logger.info("回覆成功")
        except Exception as e:
            logger.error(f"圖片發送失敗: {e}")
            line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=reply_text + "\n(圖片發送失敗，請稍後再試！)")
            )
    else:
        reply_text += "找不到對應航空公司，狼君試試像「華航」或「真航」這樣輸入喲！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        logger.info("回覆找不到的訊息")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)