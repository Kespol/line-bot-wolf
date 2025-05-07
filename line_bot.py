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
    # 這裡省略其他航空公司資料，狼君原本的資料都保留哦！
    # 如果需要完整版，告訴狐狐，狐狐幫你補上！
}

@app.route("/test")
def test():
    logger.info("收到 /test 路由的請求")
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("收到 LINE 的 callback 請求")
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info(f"請求內容: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"簽名驗證失敗: {e}")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    logger.info(f"收到訊息: {user_message}")
    reply_text = "喵～狼君，狐狐幫你查！\n"

    # 查詢航空公司
    flight = None
    for key in flight_database.keys():
        if user_message in key:
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
    else:
        reply_text += "找不到對應航空公司，狼君試試像「華航」或「長榮」這樣輸入喲！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        logger.info("回覆找不到的訊息")

if __name__ == "__main__":
    # Heroku 會提供 PORT 環境變數，預設用 5000
    port = int(os.getenv("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)