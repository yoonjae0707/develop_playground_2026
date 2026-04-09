import http.server
import socketserver
import json
import threading
import time
import random
import os
import webbrowser

PORT = 8000

# 1. 은행 데이터 (실존 은행 패러디)
def generate_banks():
    bank_names = [
        ("구한은행", "gu"), ("KD국대은행", "si"),
        ("토스트뱅크", "wo"), ("NC농촌은행", "no"),
    ]
    return [{"id": b_id, "name": name, "interest": round(random.uniform(0.02, 0.12), 3), 
             "limit": random.randint(10, 50) * 1000000} for name, b_id in bank_names]

# 2. 주식 종목 (실존 기업 패러디)
def generate_stocks():
    stock_configs = [
        ("오성전자", 72000, 0.05), ("현소자동차", 240000, 0.07), ("AK바이닉스", 180000, 0.08),
        ("NEVER", 190000, 0.06), ("KOKOA", 50000, 0.12), ("LZ생활건강", 450000, 0.07),
        ("BOSCO제철", 380000, 0.06), ("DNS대구네트워크솔루션", 600000, 0.25), ("KJ바이오로직스", 170000, 0.15),
        ("대한우주항공", 25000, 0.09), ("한수에어로", 150000, 0.18), ("BRICKITON", 220000, 0.14),
        ("NF소프트", 180000, 0.20), ("XU디자인랩", 200000, 0.15), ("이해로보틱스", 80000, 0.22)
    ]
    return [{"id": i, "name": name, "base_price": base, "price": base, "rate": 0.0, "volatility": vol} 
            for i, (name, base, vol) in enumerate(stock_configs, 1)]

banks_data = generate_banks()
stocks_data = generate_stocks()

# 초기 포트폴리오 설정 (평단가 저장을 위한 구조 변경)
portfolio = {
    "cash": 10000000,
    "loans": { bank["id"]: 0 for bank in banks_data },
    "holdings": { str(stock["id"]): {"amount": 0, "avg_price": 0} for stock in stocks_data }
}

# 3. 시장 시뮬레이션 (로컬 랜덤 변동)
def market_simulation():
    tick = 0
    while True:
        time.sleep(2.0)
        tick += 1
        for stock in stocks_data:
            change_percent = random.uniform(-stock["volatility"], stock["volatility"]) + 0.001
            new_price = int(stock["price"] * (1 + change_percent))
            stock["price"] = max((new_price // 10) * 10, 500)
            stock["rate"] = round(((stock["price"] - stock["base_price"]) / stock["base_price"]) * 100, 2)
            
        if tick % 10 == 0:
            for bank in banks_data:
                b_id = bank["id"]
                if portfolio["loans"][b_id] > 0:
                    portfolio["loans"][b_id] += int(portfolio["loans"][b_id] * (bank["interest"] / 10))

class GameRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
        
    def _send_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            if os.path.exists('index.html'):
                with open('index.html', 'rb') as f: self.wfile.write(f.read())
            else:
                self.wfile.write(b"<h1>AI Stock Game Running</h1>")
            return
            
        if self.path == '/api/state':
            # 보유 종목의 실시간 수익 현황 계산
            enriched_holdings = {}
            for s_id, data in portfolio["holdings"].items():
                if data["amount"] > 0:
                    stock = next(s for s in stocks_data if str(s["id"]) == s_id)
                    current_val = stock["price"] * data["amount"]
                    buy_val = data["avg_price"] * data["amount"]
                    profit = current_val - buy_val
                    profit_rate = round((profit / buy_val) * 100, 2) if buy_val > 0 else 0
                    
                    enriched_holdings[s_id] = {
                        **data,
                        "current_price": stock["price"],
                        "profit": profit,
                        "profit_rate": profit_rate
                    }
                else:
                    enriched_holdings[s_id] = data

            self._send_response({
                "market": stocks_data,
                "portfolio": {**portfolio, "holdings": enriched_holdings},
                "banks": banks_data
            })
            return

    def do_POST(self):
        if self.path == '/api/action':
            content_length = int(self.headers['Content-Length'])
            req = json.loads(self.rfile.read(content_length).decode('utf-8'))
            action = req.get('action')
            
            # 대출/상환 처리
            if action in ['loan', 'repay']:
                bank_id = req.get('bank_id')
                bank = next((b for b in banks_data if b["id"] == bank_id), None)
                if action == 'loan':
                    portfolio["cash"] += bank["limit"]; portfolio["loans"][bank_id] = bank["limit"]
                    return self._send_response({"success": True, "message": f"{bank['name']} 대출 완료"})
                else:
                    debt = portfolio["loans"][bank_id]
                    if portfolio["cash"] < debt: return self._send_response({"success": False, "message": "잔액 부족"})
                    portfolio["cash"] -= debt; portfolio["loans"][bank_id] = 0
                    return self._send_response({"success": True, "message": "상환 완료"})

            # 주식 매수/매도 (평단가 계산 로직 포함)
            stock_id = str(req.get('id'))
            amount = int(req.get('amount', 0))
            stock = next((s for s in stocks_data if str(s["id"]) == stock_id), None)

            if action == 'buy':
                total_cost = stock["price"] * amount
                if portfolio["cash"] < total_cost: return self._send_response({"success": False, "message": "예수금 부족"})
                
                curr_h = portfolio["holdings"][stock_id]
                new_amount = curr_h["amount"] + amount
                # 평단가 공식: (기존총액 + 신규총액) / 전체수량
                new_avg = ((curr_h["avg_price"] * curr_h["amount"]) + total_cost) / new_amount
                
                portfolio["cash"] -= total_cost
                portfolio["holdings"][stock_id] = {"amount": new_amount, "avg_price": int(new_avg)}
                self._send_response({"success": True, "message": f"{stock['name']} {amount}주 매수 완료"})
            
            elif action == 'sell':
                curr_h = portfolio["holdings"][stock_id]
                if curr_h["amount"] < amount: return self._send_response({"success": False, "message": "보유량 부족"})
                
                portfolio["cash"] += stock["price"] * amount
                curr_h["amount"] -= amount
                if curr_h["amount"] == 0: curr_h["avg_price"] = 0 # 전량 매도 시 평단가 초기화
                self._send_response({"success": True, "message": f"{stock['name']} {amount}주 매도 완료"})

if __name__ == '__main__':
    threading.Thread(target=market_simulation, daemon=True).start()
    server = socketserver.ThreadingTCPServer(('', PORT), GameRequestHandler)
    print(f"======== AI 주식 시뮬레이터 (수익률 추적 모드) ========")
    threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(f'http://127.0.0.1:{PORT}'))).start()
    try: server.serve_forever()
    except: server.socket.close()
