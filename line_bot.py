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

# ====================== 管理員狀態管理 ======================
ADMIN_USER_ID = "Ub708c5cb86181ccf095998112faf6d89"
admin_state = {}

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

    # ==================== 管理員狀態處理（含取消） ====================
    if user_id == ADMIN_USER_ID and user_id in admin_state:
        state = admin_state[user_id]

        if original_message == "取消":
            del admin_state[user_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已取消操作"))
            return

        # 新增航空公司
        if state["action"] == "add":
            step = state["step"]
            data = state["data"]

            if step == 0:
                data["name"] = original_message
                state["step"] = 1
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入拖桿類型（例如：TIAS、CAL、天際）"))
                return
            elif step == 1:
                data["towbar"] = original_message
                state["step"] = 2
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="耳機員？（需要 / 不需要）"))
                return
            elif step == 2:
                data["headset"] = original_message
                state["step"] = 3
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="bypass pin？（需要 / 不需要）"))
                return
            elif step == 3:
                data["bypass_pin"] = original_message
                state["step"] = 4
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="收裝 gear pin？（需要 / 不需要）"))
                return
            elif step == 4:
                data["gear_pin"] = original_message
                state["step"] = 5
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="清廁？（需要 / 不需要 / on call）"))
                return
            elif step == 5:
                data["toilet_service"] = original_message
                state["step"] = 6
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="飲水？（需要 / 不需要 / on call）"))
                return
            elif step == 6:
                data["water_service"] = original_message
                state["step"] = 7
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="其他要求？（直接輸入文字）"))
                return
            elif step == 7:
                data["others"] = original_message
                state["step"] = 8
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="輪檔圖片網址？（可直接貼 Google Drive 連結，或輸入「無」）"))
                return
            elif step == 8:
                data["chock_image"] = "" if original_message.lower() == "無" else original_message

                summary = f"請確認以下資料是否正確：\n\n"
                summary += f"航空公司：{data['name']}\n"
                summary += f"拖桿：{data['towbar']}\n"
                summary += f"耳機員：{data['headset']}\n"
                summary += f"bypass pin：{data['bypass_pin']}\n"
                summary += f"gear pin：{data['gear_pin']}\n"
                summary += f"清廁：{data['toilet_service']}\n"
                summary += f"飲水：{data['water_service']}\n"
                summary += f"其他要求：{data['others']}\n"
                summary += f"輪檔圖片：{data.get('chock_image', '無')}\n\n"
                summary += "請輸入「確認」儲存，或「取消」放棄"

                state["step"] = 9
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=summary))
                return

            elif step == 9:
                if original_message == "確認":
                    flight_database[data["name"]] = {
                        "towbar": data["towbar"],
                        "headset": data["headset"],
                        "bypass_pin": data["bypass_pin"],
                        "gear_pin": data["gear_pin"],
                        "toilet_service": data["toilet_service"],
                        "water_service": data["water_service"],
                        "others": data["others"],
                        "chock_image": data.get("chock_image", "")
                    }
                    save_flight_database()
                    del admin_state[user_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已成功新增「{data['name']}」"))
                else:
                    del admin_state[user_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已取消新增"))
                return

        # 移除航空公司
        if state["action"] == "remove":
            if original_message.lower() == "全部":
                flight_database.clear()
                save_flight_database()
                del admin_state[user_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已移除全部航空公司資料"))
            else:
                if original_message in flight_database:
                    del flight_database[original_message]
                    save_flight_database()
                    del admin_state[user_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已移除「{original_message}」"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到「{original_message}」"))
            return

    # ==================== 一般管理員指令 ====================
    if user_id == ADMIN_USER_ID:
        if original_message == "新增":
            admin_state[user_id] = {"action": "add", "step": 0, "data": {}}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入航空公司名稱（輸入「取消」可隨時退出）"))
            return

        if original_message == "移除":
            admin_state[user_id] = {"action": "remove", "step": 0}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入要移除的航空公司名稱（或輸入「全部」移除所有，輸入「取消」退出）"))
            return

        # ==================== 更新 ====================
        if original_message.startswith("更新 "):
            try:
                parts = original_message.split(" ", 3)
                if len(parts) < 4:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤！正確格式：更新 航空公司 欄位 新內容"))
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
                    if target_key: break

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

                if field == "chock_image" and "drive.google.com/file/d/" in new_value:
                    try:
                        file_id = new_value.split("/file/d/")[1].split("/")[0]
                        new_value = f"https://drive.google.com/uc?export=view&id={file_id}"
                    except:
                        pass

                old_value = flight_database[target_key][field]
                flight_database[target_key][field] = new_value
                save_flight_database()

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"✅ 更新成功！\n\n航空公司：{target_key}\n欄位：{field}\n原本內容：{old_value}\n新內容：{new_value}")
                )
                return
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"更新失敗：{str(e)}"))
                return

        # ==================== 加入別名（已修正儲存） ====================
        if original_message.startswith("加入別名 "):
            try:
                parts = original_message.split(" ", 2)
                if len(parts) < 3:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤！正確格式：加入別名 航空公司 別名"))
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
                    if target_key: break

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
                    TextSendMessage(text=f"✅ 已成功加入別名！\n\n航空公司：{target_key}\n新增別名：{new_alias}\n目前別名：{flight_database[target_key]['aliases']}")
                )
                return
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"加入別名失敗：{str(e)}"))
                return

        # ==================== 幫助 ====================
        if original_message in ["幫助", "功能", "指令"]:
            help_text = (
                "🛠️ 管理員功能列表\n\n"
                "【指令】\n"
                "• 新增\n"
                "• 移除\n"
                "• 更新 航空公司 欄位 新內容\n"
                "• 加入別名 航空公司 別名\n"
                "• 幫助\n\n"
                "輸入「取消」可隨時退出新增/移除流程"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
            return

    # ==================== 一般查詢 ====================
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
        reply_text += "狐狐提醒：狼君，工作時小心點，狐狐在妖怪森林等你喲～"

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