"""
JwNavigator Icon Library

Icon : 閉じる (G08)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+5, y+5, x+19, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+19, y+5, x+5, y+19,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
