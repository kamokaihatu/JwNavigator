"""
JwNavigator Icon Library

Icon : トロフィー (G84)
Size : 24x24
Style: 操作の前後を描く(破線=操作前/参照, 太線・塗り=結果, 点=クリック点)
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    canvas.create_line(
        x+6, y+3, x+18, y+3, x+18, y+9, x+12, y+14, x+6, y+9, x+6, y+3,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_arc(
        x+1, y+3, x+9, y+11,
        start=90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_arc(
        x+15, y+3, x+23, y+11,
        start=-90, extent=180,
        style=tk.ARC, outline="black", width=2
    )

    canvas.create_line(
        x+12, y+14, x+12, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+7, y+21, x+17, y+21,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9, y+18, x+15, y+18,
        width=2, fill="black", capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
