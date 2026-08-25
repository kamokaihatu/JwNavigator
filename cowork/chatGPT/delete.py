"""
JwNavigator Icon Library
Icon : Delete (高視認性 消去・線幅統一 縦線入りゴミ箱仕様)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 全体の主要な線幅を「2」に美しくマージ（統一）し、縦線を追加してリアル化します
    
    # 1. ゴミ箱の本体バケツ（width=2 で完全統一）
    canvas.create_rectangle(
        x+6, y+8,
        x+18, y+21,
        fill="",
        width=2
    )
    
    # 2. フタのフチ（横一文字の線）
    canvas.create_line(
        x+4, y+8,
        x+20, y+8,
        width=2
    )
    
    # 3. フタの上の持ち手（ここも width=2 に統一して調和させます）
    canvas.create_rectangle(
        x+10, y+4,
        x+14, y+8,
        fill="",
        width=2
    )
    
    # 4. ★あなたのご提案！バケツの中にスッと通る、美しい2本の縦線（スリット）
    canvas.create_line(x+10, y+11, x+10, y+18, width=1) # 左の縦線
    canvas.create_line(x+14, y+11, x+14, y+18, width=1) # 右の縦線
