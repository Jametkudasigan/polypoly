# 🤖 Polymarket BTC Up/Down 5-Minute Automation Bot

Bot automation untuk trading market BTC Up/Down 5 menit di Polymarket menggunakan strategy RSI-based momentum.

## 📋 Fitur

- **RSI Analysis**: Menggunakan Yahoo Finance untuk analisis momentum BTC 5-menit
- **Auto Scanning**: Scanning market BTC Up/Down 5 menit otomatis
- **Auto Entry**: Eksekusi entry berdasarkan sinyal RSI
- **Auto Exit**: Cash out otomatis ketika market resolved
- **Gasless Trading**: Menggunakan Polymarket Relayer (tidak perlu POL untuk gas)

## 🧠 Strategy

### RSI-Based Momentum
- **RSI < 30**: BUY UP (oversold, expect rebound)
- **RSI > 70**: BUY DOWN (overbought, expect pullback)
- **RSI 30-70**: SKIP (neutral)

### Entry Rules
- Threshold Price: 0.45 - 0.55
- Time Filter: 2-10 menit (sweet spot)
- Position Size: $1 per trade


## 🚀 Setup & Installation

Clone Repository
```bash
git clone https://github.com/Jametkudasigan/polypoly.git
cd polypoly
```

Install dependencies
```
python3 -m venv venv
```
```
source venv/bin/activate
```

```
pip install -r requirements.txt
```

Konfigurasi Environment
```
nano config/.env
```
buat folder log
```
mkdir -p /home/ubuntu/polypoly/logs
```

Dapatkan Credentials dari Polymarket
Untuk Email/Magic Wallet:
1. 
Login ke Polymarket
2. 
Go to Settings → Private Key
3. 
Export private key
4. 
Copy Proxy Wallet Address dari Settings

RUN BOT
```
python src/bot.py
```
