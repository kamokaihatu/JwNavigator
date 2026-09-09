"""
JwNavigator Icon Library

Icon : 鉛直角 (C050)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+16, x+21, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+12, y+12, x+8.35, y+3.8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14.3, y+11, x+13.3, y+8.7, x+11, y+9.7,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10.5, y+10.5, x+13.5, y+13.5,
        fill="black", outline=""
    )
