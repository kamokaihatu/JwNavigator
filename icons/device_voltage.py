"""
JwNavigator Icon Library

Icon : 電圧 (G60)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+13, y+2, x+7, y+13, x+12, y+13, x+10, y+22, x+17, y+10, x+12, y+10, x+13, y+2,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
