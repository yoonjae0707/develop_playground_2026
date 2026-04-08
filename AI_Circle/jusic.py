import http.server
import socketserver
import json
import threading
import time
import random
import os
import webbrowser

PORT = 8000

# 은행 정보 초기화 (대출 한도 500만~5000만 원, 이율 1% ~ 10% 랜덤)
def generate_banks():
    return [
        {"id": "gu", "name": "구한은행", "interest": round(random.uniform(0.01, 0.10), 3), "limit": random.randint(5, 50) * 1000000},
        {"id": "si", "name": "시민은행", "interest": round(random.uniform(0.01, 0.10), 3), "limit": random.randint(5, 50) * 1000000},
        {"id": "mo", "name": "모두은행", "interest": round(random.uniform(0.01, 0.10), 3), "limit": random.randint(5, 50) * 1000000},
    ]

banks_data = generate_banks()

# 초기 자본 및 상태 설정
portfolio = {
    "cash": 10000000,  # 1천만원 시작
    "loans": { "gu": 0, "si": 0, "mo": 0 }, # 은행별 기대출액
    "holdings": { str(i): 0 for i in range(1, 6) }
}

# 5가지 가상 주식 종목 (1,000 ~ 1,000,000원 사이, +-10% 변동률)
stocks_data = [
    {"id": 1, "name": "오성전자", "base_price": 75000, "price": 75000, "rate": 0, "volatility": 0.1},
    {"id": 2, "name": "현소자동차", "base_price": 250000, "price": 250000, "rate": 0, "volatility": 0.1},
    {"id": 3, "name": "AK바이닉스", "base_price": 140000, "price": 140000, "rate": 0, "volatility": 0.1},
    {"id": 4, "name": "SG생활건강", "base_price": 850000, "price": 850000, "rate": 0, "volatility": 0.1},
    {"id": 5, "name": "네버(Never)", "base_price": 180000, "price": 180000, "rate": 0, "volatility": 0.1},
]

# 주식 및 대출이자 변동 로직 (백그라운드 스레드)
def market_simulation():
    tick = 0
    while True:
        time.sleep(1.5)  # 1.5초마다 가격 변동
        tick += 1
        
        # 1. 주식 가격 변동 (+- 10% 내외)
        for stock in stocks_data:
            change_percent = random.uniform(-stock["volatility"], stock["volatility"])
            new_price = int(stock["price"] * (1 + change_percent))
            # 주가가 1,000원 밑으로 내려가지 않게 방어 (사용자 요청 범위 고려)
            stock["price"] = max(new_price, 1000)
            # 기준가 대비 수익률 계산
            stock["rate"] = ((stock["price"] - stock["base_price"]) / stock["base_price"]) * 100
            
        # 2. 대출 이자 증가 (5틱 = 7.5초 마다 한 번씩 이자 발생 적용)
        if tick % 5 == 0:
            for bank in banks_data:
                b_id = bank["id"]
                current_loan = portfolio["loans"][b_id]
                if current_loan > 0:
                    # 복리로 이자 부과 (게임적 허용으로 빠르게 증가)
                    interest_amount = int(current_loan * bank["interest"])
                    portfolio["loans"][b_id] += interest_amount

class GameRequestHandler(http.server.BaseHTTPRequestHandler):
    
    # 로깅 비활성화 (콘솔에 너무 많은 로그가 찍히는 것을 방지)
    def log_message(self, format, *args):
        pass
        
    def _send_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        # HTML 서빙
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(base_dir, 'index.html'), 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.wfile.write(f"Error loading index.html: {e}".encode('utf-8'))
            return
            
        # 상태 API
        if self.path == '/api/state':
            data = {
                "market": stocks_data,
                "portfolio": portfolio,
                "banks": banks_data
            }
            self._send_response(data)
            return
            
        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == '/api/action':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            
            action = req.get('action')
            
            # 대출 처리
            if action == 'loan':
                bank_id = req.get('bank_id')
                bank = next((b for b in banks_data if b["id"] == bank_id), None)
                if not bank:
                    self._send_response({"success": False, "message": "은행을 찾을 수 없습니다."}, 404)
                    return
                
                if portfolio["loans"][bank_id] > 0:
                    self._send_response({"success": False, "message": "이미 해당 은행의 대출이 존재합니다. 먼저 상환하세요."})
                    return
                    
                loan_amount = bank["limit"]
                portfolio["cash"] += loan_amount
                portfolio["loans"][bank_id] = loan_amount
                self._send_response({"success": True, "message": f"{bank['name']}에서 {loan_amount:,}원이 대출되었습니다."})
                return

            # 대출 상환
            if action == 'repay':
                bank_id = req.get('bank_id')
                bank = next((b for b in banks_data if b["id"] == bank_id), None)
                if not bank:
                    self._send_response({"success": False, "message": "은행을 찾을 수 없습니다."}, 404)
                    return
                
                debt = portfolio["loans"][bank_id]
                if debt <= 0:
                    self._send_response({"success": False, "message": "상환할 대출금이 없습니다."})
                    return
                    
                if portfolio["cash"] < debt:
                    self._send_response({"success": False, "message": f"잔고가 부족합니다. 상환에 필요한 금액: {debt:,}원"})
                    return
                    
                portfolio["cash"] -= debt
                portfolio["loans"][bank_id] = 0
                self._send_response({"success": True, "message": f"{bank['name']} 대출 전액 상환 완료!"})
                return

            # 주식 매수/매도
            stock_id = req.get('id')
            amount = int(req.get('amount', 0))
            
            if not stock_id or amount <= 0:
                self._send_response({"success": False, "message": "잘못된 요청입니다."}, 400)
                return
                
            stock = next((s for s in stocks_data if s["id"] == stock_id), None)
            if not stock:
                self._send_response({"success": False, "message": "종목을 찾을 수 없습니다."}, 404)
                return

            if action == 'buy':
                total_cost = stock["price"] * amount
                if portfolio["cash"] < total_cost:
                    self._send_response({"success": False, "message": "잔고가 부족합니다."})
                    return
                portfolio["cash"] -= total_cost
                portfolio["holdings"][str(stock_id)] += amount
                self._send_response({"success": True, "message": f"[{stock['name']}] {amount}주 매수 완료!"})
            
            elif action == 'sell':
                current_holdings = portfolio["holdings"][str(stock_id)]
                if current_holdings < amount:
                    self._send_response({"success": False, "message": "보유 주식이 부족합니다."})
                    return
                total_revenue = stock["price"] * amount
                portfolio["cash"] += total_revenue
                portfolio["holdings"][str(stock_id)] -= amount
                self._send_response({"success": True, "message": f"[{stock['name']}] {amount}주 매도 완료!"})
            
            else:
                self._send_response({"success": False, "message": "알 수 없는 액션입니다."})

if __name__ == '__main__':
    market_thread = threading.Thread(target=market_simulation)
    market_thread.daemon = True
    market_thread.start()
    
    class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        allow_reuse_address = True

    try:
        server = ThreadingServer(('', PORT), GameRequestHandler)
        print(f"======== AI CH0 주식 게임 ========")
        print(f"서버가 포트 {PORT} 에서 실행 중입니다.")
        print(f"브라우저에서 http://127.0.0.1:{PORT} 로 접속하세요.")
        
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://127.0.0.1:{PORT}')
            
        threading.Thread(target=open_browser).start()
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.socket.close()
