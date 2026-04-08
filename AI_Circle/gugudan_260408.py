import tkinter as tk
from tkinter import messagebox
import random
import time

class GuguDanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("구구단 마스터")
        self.root.geometry("300x350")
        self.root.eval('tk::PlaceWindow . center') # 창을 화면 중앙에 띄웁니다
        
        self.score = 0
        self.num_questions = 10
        self.current_q = 0
        self.start_time = 0
        self.min_dan = 2
        self.max_dan = 9
        self.answer = 0
        
        # 1. 난이도 선택 화면 (초기 화면)
        self.frame_diff = tk.Frame(root)
        self.frame_diff.pack(expand=True)
        
        tk.Label(self.frame_diff, text="✖️ 구구단 마스터 ✖️", font=("Helvetica", 16, "bold")).pack(pady=20)
        tk.Label(self.frame_diff, text="난이도를 선택하세요", font=("Helvetica", 10)).pack(pady=5)
        
        tk.Button(self.frame_diff, text="🌱 초급 (2~5단)", font=("Helvetica", 11), width=15, 
                  command=lambda: self.start_game(2, 5)).pack(pady=5)
        tk.Button(self.frame_diff, text="🚀 중급 (2~9단)", font=("Helvetica", 11), width=15, 
                  command=lambda: self.start_game(2, 9)).pack(pady=5)
        tk.Button(self.frame_diff, text="🔥 고급 (2~19단)", font=("Helvetica", 11), width=15, 
                  command=lambda: self.start_game(2, 19)).pack(pady=5)
        
        # 2. 실제 게임 화면
        self.frame_game = tk.Frame(root)
        
        self.lbl_status = tk.Label(self.frame_game, text="문제 1 / 10", font=("Helvetica", 10))
        self.lbl_status.pack(pady=10)
        
        self.lbl_question = tk.Label(self.frame_game, text="", font=("Helvetica", 24, "bold"))
        self.lbl_question.pack(pady=15)
        
        # 입력칸
        self.entry_answer = tk.Entry(self.frame_game, font=("Helvetica", 20), justify="center", width=8)
        self.entry_answer.pack(pady=5)
        self.entry_answer.bind("<Return>", self.check_answer) # 엔터키를 누르면 정답 확인
        
        # 확인 버튼
        self.btn_submit = tk.Button(self.frame_game, text="정답 확인", font=("Helvetica", 11), command=self.check_answer)
        self.btn_submit.pack(pady=10)
        
        # 정답/오답 결과 텍스트
        self.lbl_feedback = tk.Label(self.frame_game, text="", font=("Helvetica", 11, "bold"))
        self.lbl_feedback.pack(pady=5)
        
    def start_game(self, min_dan, max_dan):
        self.min_dan = min_dan
        self.max_dan = max_dan
        self.score = 0
        self.current_q = 1
        self.start_time = time.time()
        
        # 화면 전환: 난이도 화면 숨기고, 게임 화면 출력
        self.frame_diff.pack_forget()
        self.frame_game.pack(expand=True)
        
        self.next_question()
        
    def next_question(self):
        # 10문제를 다 풀었으면 종료 처리
        if self.current_q > self.num_questions:
            self.end_game()
            return

        self.lbl_status.config(text=f"문제 {self.current_q} / {self.num_questions}")
        
        num1 = random.randint(self.min_dan, self.max_dan)
        # 고급(19단) 난이도 처리를 위한 조건
        num2 = random.randint(1, 9) if self.max_dan <= 9 else random.randint(1, 19)
        self.answer = num1 * num2
        
        self.lbl_question.config(text=f"{num1} x {num2} = ?")
        self.entry_answer.delete(0, tk.END)
        self.entry_answer.focus() # 문제 나올때 커서 자동 활성화
        self.lbl_feedback.config(text="") # 피드백 초기화
        
    def check_answer(self, event=None):
        user_input = self.entry_answer.get().strip()
        if not user_input:
            return
            
        try:
            val = int(user_input)
        except ValueError:
            self.lbl_feedback.config(text="⚠️ 숫자만 입력하세요!", fg="orange")
            return
            
        if val == self.answer:
            self.score += 10
            self.lbl_feedback.config(text="⭕ 정답!", fg="green")
            self.root.update()
            time.sleep(0.3) # 정답인 경우 살짝만 딜레이
        else:
            self.lbl_feedback.config(text=f"❌ 틀렸습니다! 정답: {self.answer}", fg="red")
            self.root.update()
            time.sleep(0.8) # 틀렸을 때는 정답을 확인할 수 있도록 조금 더 대기
            
        self.current_q += 1
        self.next_question()
        
    def end_game(self):
        time_taken = round(time.time() - self.start_time, 2)
        
        msg = f"🎯 최종 점수: {self.score}점\n⏱️ 소요 시간: {time_taken}초\n\n"
        if self.score == 100:
            msg += "🏆 완벽합니다! 당신은 마스터입니다!"
        elif self.score >= 80:
            msg += "🌟 훌륭합니다! 조금만 더 연습해봐요!"
        elif self.score >= 50:
            msg += "👍 참 잘했어요!"
        else:
            msg += "💪 조금만 더 연습해봐요 화이팅!"
            
        # 게임 종료 알림 팝업 창
        retry = messagebox.askyesno("게임 종료", msg + "\n\n다시 플레이 하시겠습니까?")
        if retry:
            # 팝업에서 예(Yes)를 누르면 초기 화면으로 복귀
            self.frame_game.pack_forget()
            self.frame_diff.pack(expand=True)
        else:
            # 팝업에서 아니오(No)를 누르면 프로그램 종료
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GuguDanGame(root)
    root.mainloop()
