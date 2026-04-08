import os
try:
    # 윈도우 환경에서 해상도 스케일링을 강제 인식시켜 폰트와 선(원형)의 픽셀화 깨짐을 획기적으로 개선합니다.
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import tkinter as tk
from tkinter import ttk
import random

class LadderGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎲 사다리 타기 게임 🎲")
        self.root.geometry("850x650")
        
        # 전체 윈도우 배경색 (부드러운 연회색)
        self.bg_color = "#F0F2F5"
        self.root.configure(bg=self.bg_color)
        
        # ttk 스타일 설정 (가장 현대적인 clam 테마를 베이스로 수정)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background="white")
        style.configure("Title.TLabel", background="white", font=("맑은 고딕", 12, "bold"), foreground="#333333")
        
        # 버튼을 둥글고 세련된 느낌으로
        style.configure("TButton", font=("맑은 고딕", 11, "bold"), background="#4A90E2", foreground="white", borderwidth=0, padding=8)
        style.map("TButton", background=[("active", "#357ABD")])
        style.configure("TCombobox", padding=5, font=("맑은 고딕", 10))
        
        # 트레이서용 활기찬 파스텔/네온 느낌의 색상
        self.colors = ['#FF4B4B', '#FFB347', '#FFD700', '#4CAF50', '#00BCD4', '#2196F3', '#9C27B0', '#E91E63', '#795548', '#607D8B']
        
        self.margin_top = 100
        self.margin_bottom = 100
        self.margin_side = 50
        
        self.num_players = tk.IntVar(value=6)
        self.ladder_lines = []
        
        # 메인 컨테이너 패딩
        container = ttk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 왼쪽 프레임 (캔버스 영역 카드)
        self.left_frame = tk.Frame(container, bg='white', highlightbackground="#E1E4E8", highlightthickness=1)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # 캔버스 경계선 없앰
        self.canvas = tk.Canvas(self.left_frame, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 우측 패널 (컨트롤 영역 카드)
        self.right_frame = ttk.Frame(container, style="Card.TFrame", width=240)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False) # 가로 넓이 고정
        
        # 오른쪽 패널 디자인 레이아웃 구성
        inner_frame = tk.Frame(self.right_frame, bg="white")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=20)
        
        ttk.Label(inner_frame, text="👥 인원수 선택", style="Title.TLabel").pack(anchor="w", pady=(0, 5))
        
        self.combo_num = ttk.Combobox(inner_frame, textvariable=self.num_players, values=[f"{i}명" for i in range(2, 11)], state="readonly", cursor="hand2")
        self.combo_num.pack(fill=tk.X, pady=(0, 25))
        self.combo_num.bind('<<ComboboxSelected>>', self.on_num_change)
        
        ttk.Label(inner_frame, text="🎁 결과값 입력", style="Title.TLabel").pack(anchor="w", pady=(0, 5))
        
        # 텍스트창 테두리를 깔끔하게
        text_frame = tk.Frame(inner_frame, highlightbackground="#D3D9DF", highlightthickness=1)
        text_frame.pack(fill=tk.X, pady=(0, 25))
        
        self.txt_results = tk.Text(text_frame, width=15, height=12, font=("맑은 고딕", 10), relief="flat", padx=10, pady=10)
        self.txt_results.pack(fill=tk.BOTH, expand=True)
        
        # 버튼 영역
        btn_redraw = ttk.Button(inner_frame, text="✨ 새 사다리 생성", command=lambda: self.draw_ladder(force=True), cursor="hand2")
        btn_redraw.pack(fill=tk.X, pady=(10, 5))
        
        btn_trace_all = ttk.Button(inner_frame, text="눈 전체 결과 확인", command=self.trace_all, cursor="hand2")
        btn_trace_all.pack(fill=tk.X, pady=5)
        
        self.update_results_text()
        
        # 처음 시작시 창 크기가 결정된 후 그려지도록 시간차 호출
        self.root.after(100, lambda: self.draw_ladder(force=True))
        
        # 윈도우 크기가 변할 때 사다리도 가변적으로 다시 그리게 바인딩 (Responsiveness)
        self.canvas.bind("<Configure>", self.on_resize)
        self.is_drawn = False # 초기 캔버스 사이즈 로직 제어용

    def on_resize(self, event):
        """사용자가 창 크기를 늘리거나 줄일 때 비율에 맞게 사다리를 다시 배치합니다."""
        if self.is_drawn:
            # 리사이즈 도중 렉을 줄이기 위해 After 이벤트를 덮어씌움
            if hasattr(self, '_resize_job'):
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(200, self.draw_ladder)

    def trace_all(self):
        """모든 출발점을 한 번에 클릭하는 기능"""
        n = self.num_players.get()
        for i in range(n):
            self.start_trace(i)

    def on_num_change(self, event):
        """인원수 변경 시 실행"""
        self.update_results_text()
        self.draw_ladder(force=True)

    def update_results_text(self):
        """기본 이모지를 추가하여 텍스트 결과창 채움"""
        val_str = self.combo_num.get()
        n = int(val_str.replace("명", "")) if val_str else self.num_players.get()
        self.num_players.set(n)
            
        self.txt_results.delete(1.0, tk.END)
        defaults = ["🏆 1등", "💣 꽝", "🥈 2등", "💣 꽝", "🥉 3등", "💣 꽝", "💣 꽝", "💣 꽝", "💣 꽝", "💣 꽝"]
        res = "\n".join(defaults[:n])
        self.txt_results.insert(tk.END, res)

    def draw_ladder(self, force=False):
        """사다리를 캔버스에 그리기"""
        self.canvas.update_idletasks()
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        
        # 캔버스가 작으면 아직 로드되지 않은 것
        if c_width <= 10: return
        
        self.canvas.delete("all")
        self.ladder_lines = []
        
        n = self.num_players.get()
        if n < 2: return
        
        raw_results = self.txt_results.get(1.0, tk.END).strip().split('\n')
        while len(raw_results) < n:
            raw_results.append("💣 꽝")
        self.results = raw_results[:n]
        
        self.col_w = (c_width - 2 * self.margin_side) / (n - 1)
        self.row_h = (c_height - self.margin_top - self.margin_bottom)
        self.num_levels = 13
        self.level_h = self.row_h / self.num_levels
        
        # 뼈대 사다리 색상 (연하고 모서리가 둥글게 capstyle=tk.ROUND)
        ladder_color = "#E5E7EB"
        
        for i in range(n):
            x = self.margin_side + i * self.col_w
            self.canvas.create_line(x, self.margin_top, x, c_height - self.margin_bottom, width=5, fill=ladder_color, capstyle=tk.ROUND)
            
            # --- 상단 출발 노드 (버튼 대신 예쁜 원형 그려넣기) ---
            r = 22 # 동그라미 반지름
            node_color = self.colors[i % len(self.colors)]
            
            # 원과 글씨 그리기
            circle = self.canvas.create_oval(x-r, self.margin_top-r-15, x+r, self.margin_top+r-15, fill=node_color, outline="", tags=f"start_{i}")
            text = self.canvas.create_text(x, self.margin_top-15, text=f"P{i+1}", font=("Arial", 11, "bold"), fill="white", tags=f"start_{i}")
            
            # 마우스 액션 (호버 시 윤곽선 발생, 클릭 시 애니메이션)
            self.canvas.tag_bind(f"start_{i}", "<Button-1>", lambda event, idx=i: self.start_trace(idx))
            self.canvas.tag_bind(f"start_{i}", "<Enter>", lambda event, c=circle: [self.canvas.itemconfig(c, outline="#333333", width=3), self.canvas.config(cursor="hand2")])
            self.canvas.tag_bind(f"start_{i}", "<Leave>", lambda event, c=circle: [self.canvas.itemconfig(c, outline="", width=0), self.canvas.config(cursor="")])
            
            # --- 하단 결과 텍스트 (그림자 효과) ---
            y_pos = c_height - self.margin_bottom + 35
            # 그림자 레이어
            self.canvas.create_text(x+1, y_pos+1, text=self.results[i], font=("맑은 고딕", 12, "bold"), fill="#E0E0E0")
            # 본체 레이어
            self.canvas.create_text(x, y_pos, text=self.results[i], font=("맑은 고딕", 12, "bold"), fill="#444444")

        # 가로줄(다리) 생성 
        if force or not hasattr(self, 'h_lines'):
            self.h_lines = [[False] * (n - 1) for _ in range(self.num_levels)]
            for level in range(1, self.num_levels):
                for col in range(n - 1):
                    if col > 0 and self.h_lines[level][col-1]:
                        continue
                    if random.random() < 0.45:
                        self.h_lines[level][col] = True
        
        # 가로줄 그리기
        for level in range(1, self.num_levels):
            for col in range(n - 1):
                if self.h_lines[level][col]:
                    x1 = self.margin_side + col * self.col_w
                    x2 = x1 + self.col_w
                    y = self.margin_top + level * self.level_h
                    self.canvas.create_line(x1, y, x2, y, width=5, fill=ladder_color, capstyle=tk.ROUND)
        self.is_drawn = True

    def start_trace(self, start_idx):
        color = self.colors[start_idx % len(self.colors)]
        
        path = []
        curr_col = start_idx
        n = self.num_players.get()
        c_height = self.canvas.winfo_height()
        
        path.append((self.margin_side + curr_col * self.col_w, self.margin_top))
        
        for level in range(1, self.num_levels):
            y = self.margin_top + level * self.level_h
            path.append((self.margin_side + curr_col * self.col_w, y))
            
            if curr_col > 0 and self.h_lines[level][curr_col - 1]:
                curr_col -= 1
                path.append((self.margin_side + curr_col * self.col_w, y))
            elif curr_col < n - 1 and self.h_lines[level][curr_col]:
                curr_col += 1
                path.append((self.margin_side + curr_col * self.col_w, y))
                
        path.append((self.margin_side + curr_col * self.col_w, c_height - self.margin_bottom))
        
        # 이전 선들이 겹치지 않게 애니메이션 시작
        self.animate_path(path, color, 0)

    def animate_path(self, path, color, step):
        if step < len(path) - 1:
            x1, y1 = path[step]
            x2, y2 = path[step + 1]
            
            # 이동궤적 선을 더 굵고 부드러운 형태로 렌더링
            line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=6, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            
            # 애니메이션 속도를 조금 더 경쾌하게 (100ms -> 30ms)
            self.root.after(30, lambda: self.animate_path(path, color, step + 1))

if __name__ == "__main__":
    root = tk.Tk()
    app = LadderGame(root)
    root.mainloop()
