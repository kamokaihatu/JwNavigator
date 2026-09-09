"""
JwNavigator Icon Library

Icon : 線角度 (C049)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+19, x+21, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+3, y+19, x+21, y+7,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+-4, y+12, x+10, y+26,
        start=0, extent=34,
        style=tk.ARC, outline="black", width=1
    )

    canvas.create_oval(
        x+11.5, y+10.9, x+14.5, y+13.9,
        fill="black", outline=""
    )
