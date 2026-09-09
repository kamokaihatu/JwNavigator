"""
JwNavigator Icon Library

Icon : メニュー (G31)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+4, y+6, x+20, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+12, x+20, y+12,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+18, x+20, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
