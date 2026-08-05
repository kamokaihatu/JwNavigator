"""
JwNavigator Icon Library
Icon : Block Make (高視認性 9ブロック目視格子仕様)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 中の黒塗りを完全に捨て、枠線(width=1)だけで1マスずつ描くことで、
    # 拡大時にも「9つの独立した箱が集まっていること」をハッキリ見える化します
    # マスサイズ: 4x4ピクセル / 隙間: 1ピクセル
    for r in range(3):
        for c in range(3):
            x1 = x + 5 + (c * 5)
            y1 = y + 5 + (r * 5)
            canvas.create_rectangle(
                x1, y1,
                x1+4, y1+4,
                fill="",      # 中を透明（中抜き）にして境界線を際立たせる
                width=1
            )
