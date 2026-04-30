from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import threading
import asyncio
from datetime import datetime

app = Flask(__name__)
CORS(app)

TG_TOKEN = os.environ.get('TG_TOKEN', '')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID', '')
TG_API_ID = int(os.environ.get('TG_API_ID', '0'))
TG_API_HASH = os.environ.get('TG_API_HASH', '')
BRIDGE_BOT_TOKEN = os.environ.get('BRIDGE_BOT_TOKEN', '')

signals = {
    "oracle":        {"state": "neutral", "updated": ""},
    "sqzmom":        {"state": "neutral", "updated": ""},
    "tradinglatino": {"state": "neutral", "updated": ""},
}

ORACLE_BUY    = ['compra', 'buy', 'long', 'alcista', 'entrada', 'acumular']
ORACLE_SELL   = ['venta', 'sell', 'short', 'bajista', 'salida', 'cuidado']
SQZMOM_BUY    = ['crossing up', 'cruzó arriba', 'verde', 'buy', 'compra', 'alcista']
SQZMOM_SELL   = ['crossing down', 'cruzó abajo', 'rojo', 'sell', 'venta', 'bajista']
LATINO_BUY    = ['compra', 'buy', 'long', 'alcista', 'entrada', 'acumular', 'verde']
LATINO_SELL   = ['venta', 'sell', 'short', 'bajista', 'salida', 'cuidado', 'rojo']

CHANNELS = {
    '@TradingLatino_Free': 'tradinglatino',
    '@oracle_numeris': 'oracle',
}

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass

def notify(name, state):
    emoji = "🟢" if state == "buy" else "🔴" if state == "sell" else "🟡"
    names = {
        "oracle": "Oracle Numeris",
        "sqzmom": "Squeeze Momentum",
        "tradinglatino": "Trading Latino (Jaime)"
    }
    action = "COMPRAR" if state == "buy" else "VENTA" if state == "sell" else "NEUTRO"
    send_telegram(f"{emoji} <b>DCA Intel — Señal</b>\n\n{names.get(name, name)}: <b>{action}</b>\n⏰ {datetime.now().strftime('%d/%m %H:%M')}")

def parse_signal(text, buy_words, sell_words):
    text = text.lower()
    if any(w in text for w in buy_words):
        return 'buy'
    if any(w in text for w in sell_words):
        return 'sell'
    return None

def update_signal(name, text):
    buy_words = ORACLE_BUY if name == 'oracle' else SQZMOM_BUY if name == 'sqzmom' else LATINO_BUY
    sell_words = ORACLE_SELL if name == 'oracle' else SQZMOM_SELL if name == 'sqzmom' else LATINO_SELL
    state = parse_signal(text, buy_words, sell_words)
    if state:
        signals[name]['state'] = state
        signals[name]['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify(name, state)

def start_telegram_listener():
    if not TG_API_ID or not TG_API_HASH:
        return
    try:
        from telethon import TelegramClient, events
        client = TelegramClient('session', TG_API_ID, TG_API_HASH)

        @client.on(events.NewMessage(chats=list(CHANNELS.keys())))
        async def handler(event):
            chat = await event.get_chat()
            username = getattr(chat, 'username', '')
            source = CHANNELS.get(f'@{username}', '')
            if source:
                update_signal(source, event.raw_text)

        async def run():
            await client.start()
            await client.run_until_disconnected()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run())
    except Exception as e:
        print(f"Telegram listener error: {e}")

@app.route('/')
def home():
    return jsonify({"status": "ok", "signals": signals})

@app.route('/signals', methods=['GET'])
def get_signals():
    return jsonify(signals)

@app.route('/signal/<name>', methods=['POST'])
def manual_update(name):
    if name not in signals:
        return jsonify({"error": "not found"}), 404
    state = request.json.get('state', 'neutral')
    if state not in ['buy', 'sell', 'neutral']:
        return jsonify({"error": "invalid state"}), 400
    signals[name]['state'] = state
    signals[name]['updated'] = datetime.now().strftime('%d/%m %H:%M')
    notify(name, state)
    return jsonify({"ok": True})

@app.route('/webhook/sqzmom', methods=['POST'])
def sqzmom_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', ''))
    update_signal('sqzmom', text)
    return jsonify({"ok": True})

if __name__ == '__main__':
    t = threading.Thread(target=start_telegram_listener, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
