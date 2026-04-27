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
    "oracle":  {"state": "neutral", "updated": ""},
    "sqzmom":  {"state": "neutral", "updated": ""},
    "rsi_alert": {"state": "neutral", "updated": ""},
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
    names = {"oracle": "Oracle Numeris", "sqzmom": "Squeeze Momentum", "rsi_alert": "RSI Alert"}
    action = "COMPRAR" if state == "buy" else "VENTA" if state == "sell" else "NEUTRO"
    send_telegram(f"{emoji} <b>DCA Intel</b>\n\n{names.get(name, name)}: <b>{action}</b>\n⏰ {datetime.now().strftime('%d/%m %H:%M')}")

@app.route('/')
def home():
    return jsonify({"status": "ok", "version": "1.0", "signals": signals})

@app.route('/signals', methods=['GET'])
def get_signals():
    return jsonify(signals)

@app.route('/signal/<n>', methods=['POST'])
def update_signal(name):
    if name not in signals:
        return jsonify({"error": "not found"}), 404
    state = request.json.get('state', 'neutral')
    if state not in ['buy', 'sell', 'neutral']:
        return jsonify({"error": "invalid state"}), 400
    signals[name]['state'] = state
    signals[name]['updated'] = datetime.now().strftime('%d/%m %H:%M')
    notify(name, state)
    return jsonify({"ok": True, "signal": name, "state": state})

@app.route('/webhook/oracle', methods=['POST'])
def oracle_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', '')).lower()
    if any(w in text for w in ['compra', 'buy', 'long', 'alcista']):
        signals['oracle']['state'] = 'buy'
        signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('oracle', 'buy')
    elif any(w in text for w in ['venta', 'sell', 'short', 'bajista']):
        signals['oracle']['state'] = 'sell'
        signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('oracle', 'sell')
    return jsonify({"ok": True})

@app.route('/webhook/sqzmom', methods=['POST'])
def sqzmom_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', '')).lower()
    if any(w in text for w in ['compra', 'buy', 'crossing up', 'alcista']):
        signals['sqzmom']['state'] = 'buy'
        signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('sqzmom', 'buy')
    elif any(w in text for w in ['venta', 'sell', 'crossing down', 'bajista']):
        signals['sqzmom']['state'] = 'sell'
        signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify('sqzmom', 'sell')
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
