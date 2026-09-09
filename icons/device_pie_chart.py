"""
JwNavigator Icon Library

Icon : 円グラフ (G100)
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
        x+12, y+12, x+12, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+12, x+21, y+16.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_polygon(
        x+12, y+12, x+12, y+22, x+10.26, y+21.85, x+8.58, y+21.4, x+7, y+20.66, x+5.57, y+19.66, x+4.34, y+18.43, x+3.34, y+17, x+2.6, y+15.42, x+2.15, y+13.74, x+2, y+12,
        fill="black", outline=""
    )
