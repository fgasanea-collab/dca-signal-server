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
    "ballenas":      {"state": "neutral", "updated": ""},
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
        "tradinglatino": "Trading Latino",
        "ballenas": "Ballenas 🐋"
    }
    action = "COMPRAR" if state == "buy" else "VENTA" if state == "sell" else "NEUTRO"
    send_telegram(f"{emoji} <b>DCA Intel — Señal</b>\n\n{names.get(name, name)}: <b>{action}</b>\n⏰ {datetime.now().strftime('%d/%m %H:%M')}")

def parse_signal(text):
    text = text.lower()
    # Ballenas — acumulación o distribución
    if any(w in text for w in ['moved to unknown wallet', 'cold wallet', 'acumula', 'compra', 'buy', 'long', 'alcista', 'entrada', 'subir']):
        return 'buy'
    if any(w in text for w in ['moved to exchange', 'to binance', 'to coinbase', 'venta', 'sell', 'short', 'bajista', 'salida', 'bajar']):
        return 'sell'
    return None

@app.route('/')
def home():
    return jsonify({"status": "ok", "version": "2.0", "signals": signals})

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
    """
    Endpoint universal para el bot de Telegram.
    Todos los canales reenvían acá y el servidor clasifica la señal.
    """
    data = request.json or {}
    message = data.get('message') or data.get('channel_post') or {}
    text = message.get('text', '') or message.get('caption', '')
    chat_title = message.get('chat', {}).get('title', '').lower()
