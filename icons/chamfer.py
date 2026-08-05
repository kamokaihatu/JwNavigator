"""
JwNavigator Icon Library
Icon : Chamfer (高視認性 面取・width=2適正化版)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 斜めにバッサリ切り落とされた連続線の太さを3から2へ変更
    canvas.create_line(
        x+6, y+20,   # 下端
        x+6, y+13,   # 上がり
        x+13, y+6,   # ★綺麗な斜めの面取りカット
        x+20, y+6,   # 右端
        width=2,
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND
    )
