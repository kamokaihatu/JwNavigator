"""
JwNavigator Icon Library

Icon : 写真 (G74)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+4, x+21, y+20,
        outline="black", width=2
    )

    canvas.create_oval(
        x+6.2, y+7.2, x+9.8, y+10.8,
        fill="black", outline=""
    )

    canvas.create_line(
        x+3, y+18, x+9, y+12.5, x+13, y+16, x+17, y+11, x+21, y+15,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
