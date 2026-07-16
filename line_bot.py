from dotenv import load_dotenv
load_dotenv()

import os
import json
import shutil
from flask import Flask, request, abort
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

os.makedirs("/app/data", exist_ok=True)

DATA_FILE = "/app/data/flight_database.json"
REPO_FILE = "flight_database.json"

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            flight_database = json.load(f)
    except Exception as e:
        flight_database = {}
else:
    if os.path.exists(REPO_FILE):
        try:
            shutil.copy(REPO_FILE, DATA_FILE)
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                flight_database = json.load(f)
        except:
            flight_database = {}
    else:
        flight_database = {}

def save_flight_database():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(flight_database, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(str(e))

def format_status(val):
    if val == "需要":
        return "✅"
    elif val == "不需要":
        return "❌"
    elif val == "on call":
        return "📞"
    else:
        return val

ADMIN_USER_ID = "Ub708c5cb86181ccf095998112faf6d89"
admin_state = {}

@app.route("/test")
def test():
    return "Hello, WolfLord!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except:
        abort(400)
    return 'OK', 200

@app.route("/callback", methods=['GET'])
def callback_get():
    return 'OK', 200

@app.route("/")
def root():
    return "WolfLord LINE Bot"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    lower_text = text.lower()

    # ==================== 管理員狀態處理 ====================
    if user_id == ADMIN_USER_ID and user_id in admin_state:
        state = admin_state[user_id]

        if text == "取消":
            del admin_state[user_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已取消操作"))
            return

        # 新增航空公司
        if state.get("action") == "add":
            step = state.get("step", 0)
            data = state.get("data", {})

            if step == 0:
                data["name"] = text
                state["step"] = 1
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入拖桿類型"))
                return
            elif step == 1:
                data["towbar"] = text
                state["step"] = 2
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="耳機員？（需要/不需要）"))
                return
            elif step == 2:
                data["headset"] = text
                state["step"] = 3
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="bypass pin？（需要/不需要）"))
                return
            elif step == 3:
                data["bypass_pin"] = text
                state["step"] = 4
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="gear pin？（需要/不需要）"))
                return
            elif step == 4:
                data["gear_pin"] = text
                state["step"] = 5
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="清廁？（需要/不需要/on call）"))
                return
            elif step == 5:
                data["toilet_service"] = text
                state["step"] = 6
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="飲水？（需要/不需要/on call）"))
                return
            elif step == 6:
                data["water_service"] = text
                state["step"] = 7
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="其他要求？"))
                return
            elif step == 7:
                data["others"] = text
                state["step"] = 8
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="輪檔圖片網址？（輸入「無」代表不要）"))
                return
            elif step == 8:
                data["chock_image"] = "" if text.lower() == "無" else text
                summary = (
                    f"請確認資料：\n\n"
                    f"航空公司：{data['name']}\n"
                    f"拖桿：{data['towbar']}\n"
                    f"耳機員：{data['headset']}\n"
                    f"bypass pin：{data['bypass_pin']}\n"
                    f"gear pin：{data['gear_pin']}\n"
                    f"清廁：{data['toilet_service']}\n"
                    f"飲水：{data['water_service']}\n"
                    f"其他要求：{data['others']}\n"
                    f"輪檔：{data.get('chock_image', '無')}\n\n"
                    "輸入「確認」儲存，或「取消」"
                )
                state["step"] = 9
                state["data"] = data
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=summary))
                return
            elif step == 9:
                if text == "確認":
                    flight_database[data["name"]] = data
                    save_flight_database()
                    del admin_state[user_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已新增 {data['name']}"))
                else:
                    del admin_state[user_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已取消"))
                return

        # 移除航空公司
        if state.get("action") == "remove":
            if text.lower() == "全部":
                flight_database.clear()
                save_flight_database()
                del admin_state[user_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已移除全部資料"))
            elif text in flight_database:
                del flight_database[text]
                save_flight_database()
                del admin_state[user_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已移除 {text}"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該航空公司"))
            return

    # 管理員指令
    if user_id == ADMIN_USER_ID:
        if text == "新增":
            admin_state[user_id] = {"action": "add", "step": 0, "data": {}}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入航空公司名稱"))
            return

        if text == "移除":
            admin_state[user_id] = {"action": "remove", "step": 0}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入航空公司名稱或「全部」"))
            return

        if text.startswith("更新 "):
            try:
                parts = text.split(" ", 3)
                if len(parts) < 4:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤！正確格式：更新 航空公司 欄位 新內容"))
                    return
                name, field, value = parts[1], parts[2], parts[3]

                target = None
                for k in list(flight_database.keys()):
                    if name.lower() in k.lower():
                        target = k
                        break
                if not target:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到航空公司"))
                    return

                if field == "chock_image" and "drive.google.com/file/d/" in value:
                    try:
                        fid = value.split("/file/d/")[1].split("/")[0]
                        value = f"https://drive.google.com/uc?export=view&id={fid}"
                    except:
                        pass

                flight_database[target][field] = value
                save_flight_database()
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 更新成功"))
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
            return

        if text.startswith("加入別名 "):
            try:
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤！正確格式：加入別名 航空公司 別名"))
                    return
                name, alias = parts[1], parts[2]

                target = None
                for k in list(flight_database.keys()):
                    if name.lower() in k.lower():
                        target = k
                        break
                if not target:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到航空公司"))
                    return

                if "aliases" not in flight_database[target]:
                    flight_database[target]["aliases"] = []
                if alias not in flight_database[target]["aliases"]:
                    flight_database[target]["aliases"].append(alias)
                    save_flight_database()
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 別名已加入"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="別名已存在"))
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
            return

        if text in ["幫助", "功能", "指令"]:
            msg = (
                "🛠️ 管理員功能列表\n\n"
                "• 新增\n"
                "• 移除\n"
                "• 更新 航空公司 欄位 新內容\n"
                "• 加入別名 航空公司 別名\n"
                "• 幫助"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

    # 一般查詢
    flight = None
    matched_key = None
    for key, info in flight_database.items():
        if lower_text in key.lower():
            flight = info
            matched_key = key
            break
        if info.get("aliases"):
            for a in info["aliases"]:
                if lower_text in a.lower():
                    flight = info
                    matched_key = key
                    break
        if flight:
            break

    if flight:
        reply = (
            f"航空公司：{matched_key}\n"
            f"拖桿：{flight.get('towbar', '')}\n"
            f"耳機員：{format_status(flight.get('headset', ''))}\n"
            f"bypass pin：{format_status(flight.get('bypass_pin', ''))}\n"
            f"gear pin：{format_status(flight.get('gear_pin', ''))}\n"
            f"清廁：{format_status(flight.get('toilet_service', ''))}\n"
            f"飲水：{format_status(flight.get('water_service', ''))}\n"
            f"其他要求：{flight.get('others', '')}\n"
            "華航代理的787系列：專用拖桿在A9\n"
            "狐狐提醒：工作時小心點喲～"
        )
        try:
            line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=reply),
                ImageSendMessage(
                    original_content_url=flight.get('chock_image', ''),
                    preview_image_url=flight.get('chock_image', '')
                )
            ])
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到對應航空公司"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)