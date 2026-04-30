from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

TG_TOKEN = os.environ.get('TG_TOKEN', '')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID', '')

signals = {
    "oracle":        {"state": "neutral", "updated": ""},
    "sqzmom":        {"state": "neutral", "updated": ""},
    "tradinglatino": {"state": "neutral", "updated": ""},
}

ORACLE_KEYWORDS    = ['compra', 'buy', 'long', 'alcista', 'entrada', 'venta', 'sell', 'short', 'bajista', 'salida']
SQZMOM_BUY_WORDS   = ['crossing up', 'cruzó arriba', 'verde', 'buy', 'compra', 'alcista']
SQZMOM_SELL_WORDS  = ['crossing down', 'cruzó abajo', 'rojo', 'sell', 'venta', 'bajista']
LATINO_BUY_WORDS   = ['compra', 'buy', 'long', 'alcista', 'entrada', 'acumular', 'verde']
LATINO_SELL_WORDS  = ['venta', 'sell', 'short', 'bajista', 'salida', 'cuidado', 'rojo']

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

@app.route('/')
def home():
    return jsonify({"status": "ok", "signals": signals})

@app.route('/signals', methods=['GET'])
def get_signals():
    return jsonify(signals)

@app.route('/signal/<name>', methods=['POST'])
def update_signal(name):
    if name not in signals:
        return jsonify({"error": "not found"}), 404
    state = request.json.get('state', 'neutral')
    if state not in ['buy', 'sell', 'neutral']:
        return jsonify({"error": "invalid state"}), 400
    signals[name]['state'] = state
    signals[name]['updated'] = datetime.now().strftime('%d/%m %H:%M')
    notify(name, state)
    return jsonify({"ok": True})

@app.route('/telegram/update', methods=['POST'])
def telegram_update():
    data = request.json or {}
    message = data.get('message', {})
    text = str(message.get('text', '') or message.get('caption', '')).lower()
    source = data.get('source', '')

    if source == 'oracle':
        state = parse_signal(text, ORACLE_KEYWORDS[:5], ORACLE_KEYWORDS[5:])
        if state:
            signals['oracle']['state'] = state
            signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
            notify('oracle', state)
    elif source == 'sqzmom':
        state = parse_signal(text, SQZMOM_BUY_WORDS, SQZMOM_SELL_WORDS)
        if state:
            signals['sqzmom']['state'] = state
            signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
            notify('sqzmom', state)
    elif source == 'tradinglatino':
        state = parse_signal(text, LATINO_BUY_WORDS, LATINO_SELL_WORDS)
        if state:
            signals['tradinglatino']['state'] = state
            signals['tradinglatino']['updated'] = datetime.now().strftime('%d/%m %H:%M')
            notify('tradinglatino', state)

    return jsonify({"ok": True})

@app.route('/webhook/oracle', methods=['POST'])
def oracle_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', ''))
    state = parse_signal(text, ORACLE_KEYWORDS[:5], ORACLE_KEYWORDS[5:])
    if state:
        signals['oracle']['state'] = state
        signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('oracle', state)
    return jsonify({"ok": True})

@app.route('/webhook/sqzmom', methods=['POST'])
def sqzmom_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', ''))
    state = parse_signal(text, SQZMOM_BUY_WORDS, SQZMOM_SELL_WORDS)
    if state:
        signals['sqzmom']['state'] = state
        signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('sqzmom', state)
    return jsonify({"ok": True})

@app.route('/webhook/tradinglatino', methods=['POST'])
def tradinglatino_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', ''))
    state = parse_signal(text, LATINO_BUY_WORDS, LATINO_SELL_WORDS)
    if state:
        signals['tradinglatino']['state'] = state
        signals['tradinglatino']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('tradinglatino', state)
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
