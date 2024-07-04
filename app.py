import os
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# ユーザーの利用状況を保存する辞書
user_sessions = {}

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
    user_id = event.source.user_id
    message_text = event.message.text

    if message_text == "入室":
        start_session(user_id)
    elif message_text == "退室":
        end_session(user_id)
    elif message_text == "割引":
        send_discount_info(user_id)
    elif message_text == "利用履歴":
        if is_admin(user_id):
            send_usage_history(user_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="この機能は管理者のみ利用可能です。")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="有効なコマンドを入力してください。")
        )

def start_session(user_id):
    now = datetime.now()
    user_sessions[user_id] = {"start_time": now}
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=f"利用開始時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    )

def end_session(user_id):
    if user_id in user_sessions:
        start_time = user_sessions[user_id]["start_time"]
        end_time = datetime.now()
        duration = end_time - start_time
        fee = calculate_fee(duration)
        
        line_bot_api.push_message(
            user_id,
            [
                TextSendMessage(text=f"利用終了時刻: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"),
                TextSendMessage(text=f"利用時間: {duration}"),
                TextSendMessage(text=f"料金: {fee}円")
            ]
        )
        del user_sessions[user_id]
    else:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="入室記録がありません。")
        )

def calculate_fee(duration):
    # 仮の料金計算ロジック
    hours = duration.total_seconds() / 3600
    return int(hours * 1000)  # 1時間あたり1000円と仮定

def send_discount_info(user_id):
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text="現在、3時間以上の利用で10%割引中です！")
    )

def is_admin(user_id):
    # 管理者かどうかを確認するロジック（仮実装）
    admin_ids = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]
    return user_id in admin_ids

def send_usage_history(admin_id):
    # 利用履歴を取得して送信するロジック（仮実装）
    history = "利用履歴:\n"
    for user_id, session in user_sessions.items():
        history += f"ユーザーID: {user_id}, 開始時刻: {session['start_time']}\n"
    
    line_bot_api.push_message(
        admin_id,
        TextSendMessage(text=history)
    )

if __name__ == "__main__":
    app.run()