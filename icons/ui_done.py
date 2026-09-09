"""
JwNavigator Icon Library

Icon : 完了 (G07)
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
        x+7, y+12, x+10.5, y+15.5, x+17, y+8.5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
