"""
JwNavigator Icon Library
Icon : Block Break (高視認性 9ブロック中抜き四散仕様)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 結合アイコンと全く同じサイズ・線の太さの「中抜きキューブ」が、綺麗に四散する最新座標
    
    # 1. 中心に残る1個（中抜き仕様）
    canvas.create_rectangle(x+10, y+10, x+14, y+14, fill="", width=1)
    
    # 2. 上下左右に弾け飛ぶ4個
    canvas.create_rectangle(x+10, y+3,  x+14, y+7,  fill="", width=1) # 真上
    canvas.create_rectangle(x+10, y+17, x+14, y+21, fill="", width=1) # 真下
    canvas.create_rectangle(x+3,  y+10, x+7,  y+14, fill="", width=1) # 真左
    canvas.create_rectangle(x+17, y+10, x+21, y+14, fill="", width=1) # 真右
    
    # 3. 斜め4方向に弾け飛ぶ4個
    canvas.create_rectangle(x+3,  y+3,  x+7,  y+7,  fill="", width=1) # 左上
    canvas.create_rectangle(x+17, y+3,  x+21, y+7,  fill="", width=1) # 右上
    canvas.create_rectangle(x+3,  y+17, x+7,  y+21, fill="", width=1) # 左下
    canvas.create_rectangle(x+17, y+17, x+21, y+21, fill="", width=1) # 右下
