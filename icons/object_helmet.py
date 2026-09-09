"""
JwNavigator Icon Library

Icon : ヘルメット (G87)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+4, x+21, y+22,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+2, y+13, x+22, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+2, y+13, x+2, y+16, x+22, y+16, x+22, y+13,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12, y+4, x+12, y+8,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
