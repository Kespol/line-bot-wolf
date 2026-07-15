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

# ====================== 確保資料夾存在 ======================
os.makedirs("/app/data", exist_ok=True)

# ====================== 航空公司資料庫 ======================
DATA_FILE = "/app/data/flight_database.json"
REPO_FILE = "flight_database.json"

if os.path.exists(DATA_FILE):
    # Volume 裡有檔案，直接載入
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            flight_database = json.load(f)
        logger.info("成功從 Volume 載入 flight_database.json")
    except Exception as e:
        logger.error(f"載入 Volume 內的 JSON 失敗: {e}")
        flight_database = {}
else:
    # Volume 裡沒有檔案，嘗試從 repo 複製一份
    if os.path.exists(REPO_FILE):
        try:
            import shutil
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
    """將 flight_database 儲存回 JSON 檔案"""
    try:
        with open("/app/data/flight_database.json", "w", encoding="utf-8") as f:
            json.dump(flight_database, f, ensure_ascii=False, indent=2)
        logger.info("成功儲存 flight_database.json")
    except Exception as e:
        logger.error(f"儲存 flight_database.json 失敗: {e}")

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
    user_id = event.source.user_id
    original_message = event.message.text.strip()
    user_message = original_message.lower()

    logger.info(f"收到訊息: {original_message} (User: {user_id})")

    # ====================== 管理員功能 ======================
    ADMIN_USER_ID = "Ub708c5cb86181ccf095998112faf6d89"

    # 只有管理員才能使用更新指令
    if user_id == ADMIN_USER_ID and original_message.startswith("更新 "):
        try:
            # 格式：更新 航空公司 欄位 新內容
            parts = original_message.split(" ", 3)

            if len(parts) < 4:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="格式錯誤！\n正確格式：\n更新 航空公司名稱 欄位 新內容\n\n範例：\n更新 華航 其他要求 新的備註內容")
                )
                return

            airline_name = parts[1]
            field = parts[2]
            new_value = parts[3]

            # 尋找航空公司（支援別名）
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
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"找不到航空公司：{airline_name}")
                )
                return

            # 檢查欄位是否存在
            if field not in flight_database[target_key]:
                # 嘗試常見欄位對應
                field_map = {
                    "拖桿": "towbar",
                    "耳機": "headset",
                    "耳機員": "headset",
                    "bypass": "bypass_pin",
                    "bypass pin": "bypass_pin",
                    "gear": "gear_pin",
                    "gear pin": "gear_pin",
                    "清廁": "toilet_service",
                    "飲水": "water_service",
                    "其他": "others",
                    "其他要求": "others",
                    "輪檔": "chock_image",
                    "圖片": "chock_image",
                    "chock": "chock_image"
                }
                field = field_map.get(field, field)

            if field not in flight_database[target_key]:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"找不到欄位：{field}\n可用欄位：towbar, headset, bypass_pin, gear_pin, toilet_service, water_service, others, chock_image")
                )
                return

            # 更新資料
            old_value = flight_database[target_key][field]
            flight_database[target_key][field] = new_value

            # 儲存到 Volume
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
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"更新時發生錯誤：{str(e)}")
            )
            return

    # ====================== 一般查詢功能 ======================
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