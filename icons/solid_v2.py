"""
JwNavigator Icon Library

Icon : ソリッド (C018)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_rectangle(
        x+3, y+3, x+21, y+21,
        outline="black", width=1, dash=(2, 2)
    )

    canvas.create_rectangle(
        x+6, y+6, x+18, y+18,
        fill="black", outline=""
    )
