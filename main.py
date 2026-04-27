from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Telegram config
TG_TOKEN = os.environ.get('TG_TOKEN', '')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID', '')

# Estado de señales en memoria
signals = {
    "oracle": {"state": "neutral", "updated": ""},
    "sqzmom": {"state": "neutral", "updated": ""},
    "rsi_alert": {"state": "neutral", "updated": ""},
}

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
        )
    except:
        pass

def notify_telegram(signal_name, state):
    emoji = "🟢" if state == "buy" else "🔴" if state == "sell" else "🟡"
    names = {
        "oracle": "Oracle Numeris",
        "sqzmom": "Squeeze Momentum",
        "rsi_alert": "RSI Alert"
    }
    name = names.get(signal_name, signal_name)
    action = "COMPRAR" if state == "buy" else "VENTA" if state == "sell" else "NEUTRO"
    msg = f"{emoji} <b>DCA Intel — Señal actualizada</b>\n\n{name}: <b>{action}</b>\n\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    send_telegram(msg)

@app.route('/')
def home():
    return jsonify({"status": "ok", "version": "1.0"})

@app.route('/signals', methods=['GET'])
def get_signals():
    return jsonify(signals)

@app.route('/signal/<name>', methods=['POST'])
def update_signal(name):
    if name not in signals:
        return jsonify({"error": "Signal not found"}), 404
    
    data = request.json
    state = data.get('state', 'neutral')
    
    if state not in ['buy', 'sell', 'neutral']:
        return jsonify({"error": "Invalid state"}), 400
    
    signals[name]['state'] = state
    signals[name]['updated'] = datetime.now().strftime('%d/%m %H:%M')
    
    notify_telegram(name, state)
    
    return jsonify({"ok": True, "signal": name, "state": state})

# Webhook para Oracle Numeris Telegram
@app.route('/webhook/oracle', methods=['POST'])
def oracle_webhook():
    data = request.json
    text = ""
    
    if data and 'message' in data:
        text = data['message'].get('text', '').lower()
    elif data and 'text' in data:
        text = data.get('text', '').lower()
    
    # Detectar señal de compra o venta
    if any(w in text for w in ['compra', 'buy', 'long', '🟢', 'alcista']):
        signals['oracle']['state'] = 'buy'
        signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify_telegram('oracle', 'buy')
    elif any(w in text for w in ['venta', 'sell', 'short', '🔴', 'bajista']):
        signals['oracle']['state'] = 'sell'
        signals['oracle']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify_telegram('oracle', 'sell')
    
    return jsonify({"ok": True})

# Webhook para email de TradingView (SQZMOM)
@app.route('/webhook/sqzmom', methods=['POST'])
def sqzmom_webhook():
    data = request.json or {}
    text = str(data.get('text', '') or data.get('message', '')).lower()
    
    if any(w in text for w in ['compra', 'buy', 'crossing up', 'cross up', 'alcista']):
        signals['sqzmom']['state'] = 'buy'
        signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify_telegram('sqzmom', 'buy')
    elif any(w in text for w in ['venta', 'sell', 'crossing down', 'cross down', 'bajista']):
        signals['sqzmom']['state'] = 'sell'
        signals['sqzmom']['updated'] = datetime.now().strftime('%d/%m %H:%M')
        notify_telegram('sqzmom', 'sell')
    
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
