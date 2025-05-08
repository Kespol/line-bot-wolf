from flask import Flask, request
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/test")
def test():
    logger.info("收到 /test 路由的請求")
    return "Hello, WolfLord! This is a test route!"

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("收到 LINE 的 callback 請求")
    logger.info(f"請求頭: {request.headers}")
    logger.info(f"請求內容: {request.get_data(as_text=True)}")
    return "OK", 200

@app.route("/callback", methods=['GET'])
def callback_get():
    logger.info("收到 GET 請求到 /callback")
    return "This endpoint only accepts POST requests!", 405

@app.route("/")
def root():
    logger.info("收到 GET 請求到根路徑 /")
    return "Welcome to WolfLord's LINE Bot!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)