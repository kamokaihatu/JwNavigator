"""
JwNavigator Icon Library
Icon : Corner (高視認性 コーナー・width=2適正化版)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 交わるL字の直角線を極太の3から、スマートで美しい2へリニューアル！
    canvas.create_line(
        x+6, y+20,
        x+6, y+6,
        width=2,
        capstyle=tk.ROUND
    )
    canvas.create_line(
        x+5, y+6,
        x+20, y+6,
        width=2,
        capstyle=tk.ROUND
    )
