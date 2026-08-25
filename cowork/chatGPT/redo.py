"""
JwNavigator Icon Library
Icon : Redo (高視認性 進む・先端100%完全結合版)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 1. 上側をぐるっとまたぐ、美しい半円の円弧を描く (中心12, 13 / 半径6)
    canvas.create_arc(
        x+6, y+7,
        x+18, y+19,
        start=180,
        extent=-180,
        style=tk.ARC,
        width=3
    )
    
    # 2. ★円弧の右端の先端（X=18, Y=13）と1ミリのズレもなく完全にドッキングする、下向きの矢印頭
    canvas.create_polygon(
        x+18, y+17,     # 矢印の鋭い下先端
        x+14, y+12,     # 左側のハネ
        x+22, y+12,     # 右側のハネ
        fill="black",
        width=1
    )
