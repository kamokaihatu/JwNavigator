"""
JwNavigator Icon Library
Icon : Dimension (高視認性 寸法・width=2適正化版)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 1. 左右の補助境界線をすっきり描く
    canvas.create_line(x+4, y+4, x+4, y+20, width=1)
    canvas.create_line(x+20, y+4, x+20, y+20, width=1)
    
    # 2. メインの寸法線を適正な太さ(width=2)にする
    canvas.create_line(x+4, y+12, x+20, y+12, width=2)
    
    # 3. 両端の矢印のハネ
    canvas.create_line(x+8, y+8, x+4, y+12, x+8, y+16, width=1)
    canvas.create_line(x+16, y+8, x+20, y+12, x+16, y+16, width=1)
