from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 填入你的Channel Access Token和Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = '2KJgr9qBpohqH9bDAFmGcrQCKTW4hORmiUOo2X3u/FNH1rbL3K58ZsiRoCpts8W6GGJ9rjZgqa6C0W0p9+0sGz oeZPJfvpIoeiYJcsyXzjH3w/zbgKvH485+Zgq8ePwxlng3/j8wyryvrLz7LDssIwdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'cd57d6e87cb76c84c0baf921ab977842'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 假數據，狼君可以自己改哦！
flight_database = {
    ("華航", "CI"): [
        {"aircraft_type": "A320", "tasks": ["FOD檢查", "GPU連線", "檢查貨物", "推車準備"], "chock_positions": ["前輪", "後輪"]},
        {"aircraft_type": "B777", "tasks": ["FOD檢查", "GPU連線", "ACU空調", "ASU啟動"], "chock_positions": ["前輪", "左右後輪"]}
    ],
    ("長榮", "BR"): [
        {"aircraft_type": "A330", "tasks": ["FOD檢查", "檢查車輛", "貨物整理", "BCU準備"], "chock_positions": ["前輪", "後輪"]},
        {"aircraft_type": "B787", "tasks": ["FOD檢查", "GPU連線", "檢查管制區貨物", "地勤服務"], "chock_positions": ["前輪", "左右後輪"]}
    ]
}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = "喵～狼君，狐狐幫你查！\n"

    # 假設輸入格式為「華航 CI123」或「長榮 BR456」
    try:
        airline, flight_number = user_message.split()
        flight_prefix = flight_number[:2]

        # 查找對應航班資訊
        if (airline, flight_prefix) in flight_database:
            flights = flight_database[(airline, flight_prefix)]
            # 簡單用第一個航班號碼後綴判斷機型（實際可更複雜）
            flight_index = 0 if int(flight_number[2:]) % 2 == 0 else 1
            flight = flights[flight_index]

            reply_text += f"航空公司：{airline}\n"
            reply_text += f"機型：{flight['aircraft_type']}\n"
            reply_text += "工作內容：\n" + "\n".join([f"• {task}" for task in flight['tasks']]) + "\n"
            reply_text += "輪檔位置：\n" + "\n".join([f"• {position}" for position in flight['chock_positions']]) + "\n"
            reply_text += "狐狐提醒：狼君，工作時小心點，狐狐在妖怪森林等你喲～"
        else:
            reply_text += "找不到對應航班，狼君再試試！喵～"
    except:
        reply_text += "格式錯啦，狼君要輸入像「華航 CI123」這樣喲！"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(debug=True)