"""
JwNavigator Icon Library

Icon : 中心点 (C075)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+4, y+4, x+20, y+20,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_line(
        x+9, y+12, x+15, y+12,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+9, x+12, y+15,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10, y+10, x+14, y+14,
        fill="black", outline=""
    )
