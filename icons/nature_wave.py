"""
JwNavigator Icon Library

Icon : 波 (G151)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+2, y+8, x+6, y+5, x+10, y+8, x+14, y+5, x+18, y+8, x+22, y+5,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_line(
        x+2, y+14, x+6, y+11, x+10, y+14, x+14, y+11, x+18, y+14, x+22, y+11,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )

    canvas.create_line(
        x+2, y+20, x+6, y+17, x+10, y+20, x+14, y+17, x+18, y+20, x+22, y+17,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True
    )
