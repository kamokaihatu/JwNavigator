"""
JwNavigator Icon Library

Icon : 月 (G62)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+3, y+3, x+21, y+21,
        start=60, extent=240,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+10.81, y+3.81, x+27.19, y+20.19,
        start=107.8, extent=144.4,
        style=tk.ARC, outline="black", width=2
    )
