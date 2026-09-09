"""
JwNavigator Icon Library

Icon : エラー (G06)
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
        x+8, y+8, x+16, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+8, x+8, y+16,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
