"""
JwNavigator Icon Library

Icon : 距離点 (C064)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2.5, y+12.5, x+5.5, y+15.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+4, y+14, x+21, y+14,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_oval(
        x+14, y+12, x+18, y+16,
        fill="black", outline=""
    )

    canvas.create_line(
        x+4, y+6, x+4, y+10,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+6, x+16, y+10,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+8, x+6, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+4, y+8, x+6.5, y+6.5, x+6.5, y+9.5,
        fill="black", outline=""
    )

    canvas.create_line(
        x+10, y+8, x+14, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+16, y+8, x+13.5, y+9.5, x+13.5, y+6.5,
        fill="black", outline=""
    )
