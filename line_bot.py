from flask import Flask
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    logger.info("收到 LINE 的 callback 請求")
    return "OK", 200

@app.route("/test")
def test():
    logger.info("收到 /test 路由的請求")
    return "Hello, WolfLord! This is a test route!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"啟動 Flask 應用在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)