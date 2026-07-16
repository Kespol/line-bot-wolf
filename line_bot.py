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

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 從環境變數讀取 Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ====================== 確保資料夾存在 ======================
os.makedirs("/app/data", exist_ok=True)

# ====================== 航空公司資料庫 ======================
DATA_FILE = "/app/data/flight_database.json"
REPO_FILE = "flight_database.json"

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            flight_database = json.load(f)
        logger.info("成功從 Volume 載入 flight_database.json")
    except Exception as e:
        logger.error(f"載入 Volume 內的 JSON 失敗: {e}")
        flight_database = {}
else:
    if os.path.exists(REPO_FILE):
        try:
            shutil.copy(REPO_FILE, DATA_FILE)
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                flight_database = json.load(f)
            logger.info("首次啟動，已從 repo 複製 flight_database.json 到 Volume")
        except Exception as e:
            logger.error(f"複製 JSON 失敗: {e}")
            flight_database = {}
    else:
        logger.error("找不到任何 flight_database.json，資料為空")
        flight_database = {}

# ====================== 儲存資料函數 ======================
def save_flight_database():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(flight_database, f, ensure_ascii=False, indent=2)
        logger.info("成功儲存 flight_database.json")
    except Exception as e:
        logger.error(f"儲存 flight_database.json 失敗: {e}")

# ====================== 圖示格式化函數 ======================
def format_status(val):
    if val == "需要":
        return "✅"
    elif val == "不需要":
        return "❌"
    elif val == "on call":
        return "📞"
    else:
        return val

# ====================== 路由 ======================
@app.route("/test")
def test():
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK', 200

@app.route("/callback", methods=['GET'])
def callback_get():
    return "This endpoint only accepts POST requests!", 405

@app.route("/")
def root():
    return "Welcome to WolfLord's LINE Bot!"

# ====================== 訊息處理 ======================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    original_message = event.message.text.strip()
    user_message = original_message.lower()

    logger.info(f"收到訊息: {original_message} (User: {user_id})")

    ADMIN_USER_ID = "Ub708c5cb86181ccf095998112faf6d89"

    # ---------- 幫助 ----------
    if user_id == ADMIN_USER_ID and original_message in ["幫助", "功能", "指令"]:
        help_text = (
            "🛠️ 管理員功能列表\n\n"
            "【目前可用指令】\n"
            "• 更新 航空公司 欄位 新內容\n"
            "  範例：更新 華航 其他要求 新的備註\n\n"
            "• 加入別名 航空公司 別名\n"
            "  範例：加入別名 CAL中華 華航\n\n"
            "• 幫助 / 功能 / 指令\n"
            "  → 顯示此說明"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
        return

    # ---------- 更新 ----------
    if user_id == ADMIN_USER_ID and original_message.startswith("更新 "):
        try:
            parts = original_message.split(" ", 3)
            if len(parts) < 4:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="格式錯誤！\n正確格式：\n更新 航空公司名稱 欄位 新內容")
                )
                return

            airline_name = parts[1]
            field = parts[2]
            new_value = parts[3]

            target_key = None
            for key, info in flight_database.items():
                if airline_name.lower() in key.lower():
                    target_key = key
                    break
                if "aliases" in info:
                    for alias in info.get("aliases", []):
                        if airline_name.lower() in alias.lower():
                            target_key = key
                            break
                if target_key:
                    break

            if not target_key:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到航空公司：{airline_name}"))
                return

            if field not in flight_database[target_key]:
                field_map = {
                    "拖桿": "towbar", "耳機": "headset", "耳機員": "headset",
                    "bypass": "bypass_pin", "bypass pin": "bypass_pin",
                    "gear": "gear_pin", "gear pin": "gear_pin",
                    "清廁": "toilet_service", "飲水": "water_service",
                    "其他": "others", "其他要求": "others",
                    "輪檔": "chock_image", "圖片": "chock_image", "chock": "chock_image"
                }
                field = field_map.get(field, field)

            if field not in flight_database[target_key]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到欄位：{field}"))
                return

            # 自動轉換 Google Drive 圖片網址
            if field == "chock_image" and "drive.google.com/file/d/" in new_value:
                try:
                    file_id = new_value.split("/file/d/")[1].split("/")[0]
                    new_value = f"https://drive.google.com/uc?export=view&id={file_id}"
                except Exception as e:
                    logger.error(f"轉換 Google Drive 網址失敗: {e}")

            old_value = flight_database[target_key][field]
            flight_database[target_key][field] = new_value
            save_flight_database()

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"✅ 更新成功！\n\n航空公司：{target_key}\n欄位：{field}\n原本內容：{old_value}\n新內容：{new_value}"
                )
            )
            return

        except Exception as e:
            logger.error(f"更新失敗: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"更新時發生錯誤：{str(e)}"))
            return

    # ---------- 加入別名 ----------
    if user_id == ADMIN_USER_ID and original_message.startswith("加入別名 "):
        try:
            parts = original_message.split(" ", 2)
            if len(parts) < 3:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="格式錯誤！\n正確格式：\n加入別名 航空公司 別名")
                )
                return

            airline_name = parts[1]
            new_alias = parts[2]

            target_key = None
            for key, info in flight_database.items():
                if airline_name.lower() in key.lower():
                    target_key = key
                    break
                if "aliases" in info:
                    for alias in info.get("aliases", []):
                        if airline_name.lower() in alias.lower():
                            target_key = key
                            break
                if target_key:
                    break

            if not target_key:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到航空公司：{airline_name}"))
                return

            if "aliases" not in flight_database[target_key]:
                flight_database[target_key]["aliases"] = []

            if new_alias in flight_database[target_key]["aliases"]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"「{new_alias}」已經是 {target_key} 的別名了"))
                return

            flight_database[target_key]["aliases"].append(new_alias)
            save_flight_database()

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"✅ 已成功加入別名！\n\n航空公司：{target_key}\n新增別名：{new_alias}\n目前別名：{', '.join(flight_database[target_key]['aliases'])}"
                )
            )
            return

        except Exception as e:
            logger.error(f"加入別名失敗: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"加入別名時發生錯誤：{str(e)}"))
            return

    # ---------- 一般查詢 ----------
    flight = None
    matched_key = None

    for key, info in flight_database.items():
        if user_message in key.lower():
            flight = info
            matched_key = key
            break
        if "aliases" in info:
            for alias in info.get("aliases", []):
                if user_message in alias.lower():
                    flight = info
                    matched_key = key
                    break
        if flight:
            break

    reply_text = "喵～狐狐幫你查！\n"

    if flight:
        reply_text += f"航空公司：{matched_key}\n"
        reply_text += f"拖桿：{flight['towbar']}\n"
        reply_text += f"耳機員：{format_status(flight['headset'])}\n"
        reply_text += f"bypass pin：{format_status(flight['bypass_pin'])}\n"
        reply_text += f"收裝gear pin：{format_status(flight['gear_pin'])}\n"
        reply_text += f"清廁：{format_status(flight['toilet_service'])}\n"
        reply_text += f"飲水：{format_status(flight['water_service'])}\n"
        reply_text += f"其他要求：{flight['others']}\n"
        reply_text += "華航代理的787系列：專用拖桿在A9\n"
        reply_text += "提醒：工作時小心點喲～"

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
        except Exception as e:
            logger.error(f"圖片發送失敗: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text + "\n(圖片發送失敗，請稍後再試！)")
            )
    else:
        reply_text += "找不到對應航空公司，狼君試試像「華航」或「真航」這樣輸入喲！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)