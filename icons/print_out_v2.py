"""
JwNavigator Icon Library

Icon : 印刷 (C043)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+7, y+9, x+7, y+3, x+17, y+3, x+17, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_rectangle(
        x+3, y+9, x+21, y+16,
        outline="black", width=2
    )

    canvas.create_line(
        x+7, y+16, x+7, y+21, x+17, y+21, x+17, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+19, x+15, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
