"""
JwNavigator Icon Library

Icon : ロック解除 (G23)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+5, y+11, x+19, y+21,
        outline="black", width=2
    )

    canvas.create_oval(
        x+10.4, y+14.4, x+13.6, y+17.6,
        fill="black", outline=""
    )

    canvas.create_arc(
        x+7, y+3, x+17, y+13,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+17, y+8, x+17, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
