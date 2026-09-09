"""
JwNavigator Icon Library

Icon : 属性取得 (C048)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+20, x+13, y+20,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+16, y+2, x+22, y+8,
        fill="black", outline=""
    )

    canvas.create_line(
        x+18, y+7, x+10, y+18,
        width=2.5, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+7.8, y+18.3, x+10.2, y+20.7,
        fill="black", outline=""
    )
