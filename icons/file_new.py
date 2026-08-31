"""
JwNavigator Icon Library

Icon : 新規
Size : 24x24
"""

import tkinter as tk

def draw(canvas, x=0, y=0):

    # 👑 ページ外枠が「上辺→折れ角→右辺→下辺」で終わっていて、左辺
    # （左端を閉じる縦線）がそもそも描かれていなかった。「左の縦線が
    # 消えてる」という指摘の正体はこれで、プラス記号ではなくページの
    # 外枠自体が閉じていなかった（2026-08-31）。
    canvas.create_line(
        x+6,y+3, x+14,y+3, x+18,y+7, x+18,y+21, x+6,y+21, x+6,y+3,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+14,y+3, x+14,y+7, x+18,y+7,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+9,y+13, x+15,y+13,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )

    canvas.create_line(
        x+12,y+10, x+12,y+16,
        width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND
    )
