"""
JwNavigator Icon Library

Icon : 情報 (G04)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+2, y+2, x+22, y+22,
        outline="black", width=2
    )

    canvas.create_line(
        x+12, y+11, x+12, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+10.6, y+6.1, x+13.4, y+8.9,
        fill="black", outline=""
    )
