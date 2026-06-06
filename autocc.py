import re

srt_time_pattern = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}$")

ccn = input("자막 이름: ")
with open(f"./{ccn}.srt", "a", encoding="UTF-8") as cc:

    cnt = 1
    tol = []
    ts = "00:00:00,000"

    while True:
        ly = input("가사 입력 (종료: 0): ")
        if ly == "0":
            break

        # 종료 타이밍 검사
        while True:
            te = input("종료 타이밍 (형식: 00:00:05,000): ")
            if srt_time_pattern.match(te):
                break
            else:
                print("❌ 잘못된 포맷입니다. 올바른 형식은 'HH:MM:SS,mmm'입니다 (예: 00:01:23,456)")

        # ✔ 여기서 문자열만 append
        tol.append(f"{cnt}\n{ts} --> {te}\n{ly}")
        ts = te
        cnt += 1

    # ✔ 리스트 요소가 문자열이므로 그대로 write 가능
    for entry in tol:
        cc.write(entry + "\n\n")
