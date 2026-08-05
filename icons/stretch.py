"""
JwNavigator Icon Library
Icon : Stretch (高視認性 伸縮・width=2適正化版)
Size : 24×24
"""
import tkinter as tk

def draw(canvas, x=0, y=0):
    # 1. 右側のターゲット基準線を3から2へ適正化
    canvas.create_line(
        x+18, y+3,
        x+18, y+21,
        width=2,
        capstyle=tk.ROUND
    )
    
    # 2. 左から伸びる伸縮線
    canvas.create_line(
        x+3, y+12,
        x+14, y+12,
        width=1,
        capstyle=tk.ROUND
    )
    
    # 3. 基準線に突き刺さる矢印頭
    canvas.create_polygon(
        x+11, y+8,
        x+16, y+12,
        x+11, y+16,
        fill="black"
    )
