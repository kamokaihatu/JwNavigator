"""
JwNavigator Icon Library

Icon : 範囲選択 (B14)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+3, x+17, y+17,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_rectangle(
        x+6, y+6, x+10, y+10,
        fill="black", outline=""
    )

    canvas.create_rectangle(
        x+11, y+10, x+14, y+14,
        fill="black", outline=""
    )

    canvas.create_polygon(
        x+15, y+15, x+22, y+17, x+19, y+19, x+17, y+22,
        fill="black", outline=""
    )

    canvas.create_line(
        x+19, y+19, x+22, y+22,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
