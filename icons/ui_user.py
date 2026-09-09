"""
JwNavigator Icon Library

Icon : ユーザー (G49)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_oval(
        x+7.5, y+3.5, x+16.5, y+12.5,
        outline="black", width=2
    )

    canvas.create_arc(
        x+3, y+13, x+21, y+31,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=2
    )
