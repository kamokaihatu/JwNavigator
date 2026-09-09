"""
JwNavigator Icon Library

Icon : コーヒー (G133)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+3, y+8, x+3, y+17, x+6, y+20, x+14, y+20, x+17, y+17, x+17, y+8, x+3, y+8,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+15, y+9, x+22, y+16,
        start=-90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+7, y+3, x+7, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+10, y+2, x+10, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+13, y+3, x+13, y+6,
        width=1, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
