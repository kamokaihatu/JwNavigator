"""
JwNavigator Icon Library

Icon : リスト (G30)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+3.6, y+4.6, x+6.4, y+7.4,
        fill="black", outline=""
    )

    canvas.create_line(
        x+9, y+6, x+21, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+3.6, y+10.6, x+6.4, y+13.4,
        fill="black", outline=""
    )

    canvas.create_line(
        x+9, y+12, x+21, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+3.6, y+16.6, x+6.4, y+19.4,
        fill="black", outline=""
    )

    canvas.create_line(
        x+9, y+18, x+21, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
