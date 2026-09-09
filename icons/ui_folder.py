"""
JwNavigator Icon Library

Icon : フォルダ (G13)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+7, x+3, y+19, x+21, y+19, x+21, y+9, x+11, y+9, x+9, y+6, x+3, y+6,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
