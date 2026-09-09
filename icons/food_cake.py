"""
JwNavigator Icon Library

Icon : ケーキ (G134)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+12, x+3, y+20, x+21, y+20, x+21, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+3, y+7, x+21, y+17,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+3, y+12, x+21, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+2, x+12, y+7,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10.7, y+0.7, x+13.3, y+3.3,
        fill="black", outline=""
    )

    canvas.create_line(
        x+8, y+20, x+8, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+20, x+16, y+16,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
