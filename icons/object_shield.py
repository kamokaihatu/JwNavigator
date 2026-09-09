"""
JwNavigator Icon Library

Icon : 保護 (G80)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+12, y+2, x+21, y+5, x+21, y+11, x+12, y+22, x+3, y+11, x+3, y+5, x+12, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+8, y+12, x+11, y+15, x+16, y+9,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
