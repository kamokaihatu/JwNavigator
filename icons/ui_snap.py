"""
JwNavigator Icon Library

Icon : スナップ (G42)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_arc(
        x+4, y+2, x+20, y+18,
        start=0, extent=180,
        style=tk.ARC, outline="black", width=4
    )

    canvas.create_line(
        x+6, y+10, x+6, y+20,
        width=4, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+18, y+10, x+18, y+20,
        width=4, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+4, y+17, x+8, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+16, y+17, x+20, y+17,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
