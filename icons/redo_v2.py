"""
JwNavigator Icon Library

Icon : やり直し (B15)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+6, y+7, x+18, y+19,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=3
    )

    canvas.create_polygon(
        x+18, y+17, x+22, y+12, x+14, y+12,
        fill="black", outline=""
    )
