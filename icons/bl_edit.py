"""
JwNavigator Icon Library
Icon : Block Edit (高視認性 ブロック編集・9マス完全維持外側工具仕様)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 1. 3x3（9マス）の格子を【1個も減らさずに100%完全描写】してブロックの意味をキープ！
    # マスサイズ: 4x4ピクセル / 隙間: 1ピクセル
    for r in range(3):
        for c in range(3):
            x1 = x + 3 + (c * 5) # ペンを右上に置くため、全体をほんの少しだけ左下に寄せる微調整
            y1 = y + 7 + (r * 5)
            canvas.create_rectangle(
                x1, y1,
                x1+4, y1+4,
                fill="",      # 中抜きで他のブロックアイコンとデザインを統一
                outline="black",
                width=1
            )
            
    # 2. ★新しい特等席！9マスの「外側の右上」から、マスの角を狙い撃つ「極太の編集ペン」
    # マスの線と1ミリも重ならない位置から、斜め45度で美しくアプローチします
    canvas.create_line(
        x+14, y+6,        # ペンの先端付近
        x+21, y+1,        # ペンの持ち手の後ろ
        width=3,          # 潰れを防ぐ適正な極太幅
        capstyle=tk.ROUND
    )
    
    # 3. ペンの先端（マスの角を優しく指し示すシャープな三角形）
    canvas.create_polygon(
        x+11, y+9,        # マスの右上角にツンと触れる鋭いペン先
        x+16, y+8,        # 上側のハネ
        x+13, y+5,        # 下側のハネ
        fill="black"
    )
