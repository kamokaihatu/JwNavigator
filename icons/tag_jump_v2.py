"""
JwNavigator Icon Library

Icon : タグジャンプ (C073)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_polygon(
        x+3, y+4, x+12, y+4, x+17, y+9, x+12, y+14, x+3, y+14,
        fill="", outline="black", width=2, joinstyle=tk.ROUND
    )

    canvas.create_oval(
        x+5.8, y+7.8, x+8.2, y+10.2,
        fill="black", outline=""
    )

    canvas.create_line(
        x+12, y+19, x+18.6, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+21, y+19, x+18, y+20.8, x+18, y+17.2,
        fill="black", outline=""
    )
