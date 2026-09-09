"""
JwNavigator Icon Library

Icon : 中心線 (C007)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+5, x+21, y+5,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+3, y+19, x+21, y+19,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(2, 2)
    )

    canvas.create_line(
        x+2, y+12, x+22, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, dash=(5, 2, 1, 2)
    )
