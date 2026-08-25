"""
JwNavigator Icon Library
Icon : Copy (高視認性 複写・重なり補強矢印イン仕様)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 移動アイコンと全く同じ完璧な重なり比率のまま、元も先も「実線」に統一します
    
    # 1. 複写前の元の箱「1px幅の実線（10x10サイズ）」
    canvas.create_rectangle(
        x+3, y+11,
        x+13, y+21,
        fill="",
        width=1
    )
    
    # 2. ★重なりをほんの少し多くした、複写されて増えた箱「1px幅の実線」
    canvas.create_rectangle(
        x+10, y+4,
        x+20, y+14,
        fill="",
        width=1
    )
    
    # 3. 箱の重なりを突き抜ける「細い矢印線」
    canvas.create_line(
        x+8, y+16,
        x+15, y+9,
        width=1
    )
    
    # 4. 複写先の箱の内側にすっぽり美しく収まった、シャープな矢印頭（三角形）
    canvas.create_polygon(
        x+11, y+8,    # 左側のハネ
        x+16, y+8,    # 矢印の鋭い先端
        x+16, y+13,   # 下側のハネ
        fill="black",
        width=1
    )
