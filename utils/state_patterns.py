# ===== ✂️ utils/state_patterns.py START PART 1 ✂️ =====
from enum import Enum, auto

class RuleId(Enum):
    DIM_TOOLTIP = auto()
    LINE_TOOLTIP = auto()
    RECT_TOOLTIP = auto()
    CIRCLE_TOOLTIP = auto()
    TEXT_TOOLTIP = auto()
    TWO_LINE_TOOLTIP = auto()
    CENTER_TOOLTIP = auto()
    RENTENT_TOOLTIP = auto()
    AUTO_TOOLTIP = auto()
    POINT_TOOLTIP = auto()
    SESSEN_TOOLTIP = auto()
    SETSUEN_TOOLTIP = auto()
    HATCH_TOOLTIP = auto()
    TATEG_TOOLTIP = auto()
    POLYGON_TOOLTIP = auto()
    CURVE_TOOLTIP = auto()
    RANGE_TOOLTIP = auto()
    FUKUSEN_TOOLTIP = auto()
    CORNER_TOOLTIP = auto()
    EXTEND_TOOLTIP = auto()
    CHAMFER_TOOLTIP = auto()
    DELETE_TOOLTIP = auto()
    COPY_TOOLTIP = auto()
    MOVE_TOOLTIP = auto()
    IMAGE_TOOLTIP = auto()
    HOURAKU_TOOLTIP = auto()
    BUNKATSU_TOOLTIP = auto()
    CLEANUP_TOOLTIP = auto()
    ATTRIB_TOOLTIP = auto()
    ZUGEI_TOOLTIP = auto()
    KIGOU_TOOLTIP = auto()
    COORD_TOOLTIP = auto()
    GAIBU_TOOLTIP = auto()
    SOKUTEI_TOOLTIP = auto()
    HYOU_TOOLTIP = auto()
    DIST_TOOLTIP = auto()
    SHIKI_TOOLTIP = auto()
    PARA_TOOLTIP = auto()
    REG_TOOLTIP = auto()
    DIM_ZUGEI_TOOLTIP = auto()
    DIM_BREAK_TOOLTIP = auto()
    REG_SELECT_TOOLTIP = auto()
    LINE_WAIT = auto()
    RECT_WAIT = auto()
    CIRCLE_WAIT = auto()
    TEXT_WAIT = auto()
    DIM_BRACKET = auto()
    DIM_WAIT = auto()
    TWO_LINE_WAIT = auto()
    CENTER_WAIT = auto()
    AUTO_WAIT = auto()
    POINT_WAIT = auto()
    SESSEN_WAIT = auto()
    HATCH_WAIT = auto()
    TATEG_WAIT = auto()
    RANGE_WAIT = auto()
    FUKUSEN_WAIT = auto()
    CORNER_WAIT = auto()
    EXTEND_WAIT = auto()
    CHAMFER_WAIT = auto()
    DELETE_WAIT = auto()
    IMAGE_WAIT = auto()
    HOURAKU_WAIT = auto()
    BUNKATSU_WAIT = auto()
    ATTRIB_WAIT = auto()
    KIGOU_WAIT = auto()
    COORD_WAIT = auto()
    HYOU_WAIT = auto()
    DIST_WAIT = auto()
    SHIKI_WAIT = auto()
    PARA_WAIT = auto()
    DIM_ZUGEI_WAIT = auto()
    DIM_BREAK_WAIT = auto()
    TWO_FIVE_D_WAIT = auto()
    FILE_OPEN = auto()
    FILE_SAVE = auto()
    FILE_SAVE_AS = auto()
    FILE_SAVE_OVER = auto()
    FILE_OPEN_EXIST = auto()
    FILE_NEW = auto()
# ===== ✂️ utils/state_patterns.py END PART 1 ✂️ =====

# ===== ✂️ utils/state_patterns.py START PART 2 ✂️ =====
STATE_DATABASE = {
    "STATE_LINE": [(r"線を書きます", RuleId.LINE_TOOLTIP), (r"始点を指示してください", RuleId.LINE_WAIT)],
    "STATE_RECT": [(r"矩形を書きます", RuleId.RECT_TOOLTIP), (r"矩形の基準点を指示して下さい", RuleId.RECT_WAIT)],
    "STATE_CIRCLE": [(r"円を書く", RuleId.CIRCLE_TOOLTIP), (r"中心点を指示してください", RuleId.CIRCLE_WAIT)],
    "STATE_TEXT": [(r"文字を書きます", RuleId.TEXT_TOOLTIP), (r"文字を入力するか", RuleId.TEXT_WAIT)],
    "STATE_DIM": [(r"寸法を記入します", RuleId.DIM_TOOLTIP), (r"\[寸法\]", RuleId.DIM_BRACKET), (r"寸法線の位置を指示して下さい", RuleId.DIM_WAIT)],
    "STATE_TWO_LINE": [(r"２線を作図します", RuleId.TWO_LINE_TOOLTIP), (r"基準線を指示してください", RuleId.TWO_LINE_WAIT)],
    "STATE_CENTER": [(r"中心線を作図します", RuleId.CENTER_TOOLTIP), (r"１番目の線・円をﾏ🇺🇸"[:10], RuleId.CENTER_WAIT)],
    "STATE_RENTENT": [(r"連続線・連続円弧を作図します", RuleId.RENTENT_TOOLTIP)],
    "STATE_AUTO": [(r"AUTOモードを実行します", RuleId.AUTO_TOOLTIP), (r"AUTOモード   \(L\)free", RuleId.AUTO_WAIT)],
    "STATE_POINT": [(r"点を書きます", RuleId.POINT_TOOLTIP), (r"点位置を指示してください", RuleId.POINT_WAIT)],
    "STATE_SESSEN": [(r"接線を作図します", RuleId.SESSEN_TOOLTIP), (r"円を指示してください", RuleId.SESSEN_WAIT)],
    "STATE_SETSUEN": [(r"接円を作図します", RuleId.SETSUEN_TOOLTIP)],
    "STATE_HATCH": [(r"ハッチングを行います", RuleId.HATCH_TOOLTIP), (r"閉鎖連続線・円をﾏ🇺🇸"[:10], RuleId.HATCH_WAIT)],
    "STATE_TATEG": [(r"建具を選択してください", RuleId.TATEG_WAIT), (r"ﾊﾟラメトリックな建具", RuleId.TATEG_TOOLTIP)],
    "STATE_POLYGON": [(r"多角形（２辺）を作図します", RuleId.POLYGON_TOOLTIP)],
    "STATE_CURVE": [(r"曲線を作図します", RuleId.CURVE_TOOLTIP)],
    "STATE_RANGE": [(r"範囲を指定し", RuleId.RANGE_TOOLTIP), (r"範囲選択の始点を", RuleId.RANGE_WAIT)],
    "STATE_FUKUSEN": [(r"元の線に平行な線をつくります", RuleId.FUKUSEN_TOOLTIP), (r"複線にする図形を選択", RuleId.FUKUSEN_WAIT)],
    "STATE_CORNER": [(r"２線のコーナー処理を行います", RuleId.CORNER_TOOLTIP), (r"線（Ａ）指示", RuleId.CORNER_WAIT)],
    "STATE_EXTEND": [(r"線を伸縮します", RuleId.EXTEND_TOOLTIP), (r"指示点までの伸縮線", RuleId.EXTEND_WAIT)],
    "STATE_CHAMFER": [(r"２線を面取りします", RuleId.CHAMFER_TOOLTIP), (r"面取する１番目の線", RuleId.CHAMFER_WAIT), (r"線切断（Ｒ）", RuleId.CHAMFER_WAIT)],
    "STATE_DELETE": [(r"図形を消去します", RuleId.DELETE_TOOLTIP), (r"線・円マウス\(L\)部分消し", RuleId.DELETE_WAIT)],
    "STATE_COPY": [(r"図形を複写します", RuleId.COPY_TOOLTIP)],
    "STATE_MOVE": [(r"図形を移動します", RuleId.MOVE_TOOLTIP)],
    "STATE_IMAGE": [(r"画像の挿入、サイズ調整", RuleId.IMAGE_TOOLTIP)],
    "STATE_HOURAKU": [(r"図形の外郭線をつなげて整理します", RuleId.HOURAKU_TOOLTIP), (r"包絡範囲の始点指示", RuleId.HOURAKU_WAIT)],
    "STATE_BUNKATSU": [(r"点や線の間を分割します", RuleId.BUNKATSU_TOOLTIP), (r"線・円（Ａ）指示　ﾏ🇺🇸"[:10], RuleId.BUNKATSU_WAIT)],
    "STATE_CLEANUP": [(r"データの整理をします", RuleId.CLEANUP_TOOLTIP)],
    "STATE_ATTRIB": [(r"データの属性を変更します", RuleId.ATTRIB_TOOLTIP), (r"変更するデータを指示してください", RuleId.ATTRIB_WAIT)],
    "STATE_ZUGEI": [(r"図形ファイルを読み込みます", RuleId.ZUGEI_TOOLTIP)],
    "STATE_KIGOU": [(r"線記号変形を行います", RuleId.KIGOU_TOOLTIP), (r"記号を選択してください", RuleId.KIGOU_WAIT)],
    "STATE_COORD": [(r"座標ファイルの読込・書込", RuleId.COORD_TOOLTIP), (r"項目を選択してください", RuleId.COORD_WAIT)],
    "STATE_GAIBU": [(r"外部変形を行います", RuleId.GAIBU_TOOLTIP)],
    "STATE_SOKUTEI": [(r"距離・面積・座標・角度を測定", RuleId.SOKUTEI_TOOLTIP)],
    "STATE_HYOU": [(r"表計算を行います", RuleId.HYOU_TOOLTIP), (r"範囲選択の始点をﾏ🇺🇸"[:10], RuleId.HYOU_WAIT)],
    "STATE_DIST": [(r"始点からの距離を指定して点", RuleId.DIST_TOOLTIP), (r"始点を指示してください  \(L\)free", RuleId.DIST_WAIT)],
    "STATE_SHIKI": [(r"式計算を行います", RuleId.SHIKI_TOOLTIP), (r"□□　　　項目を選択してください", RuleId.SHIKI_WAIT)],
    "STATE_PARA": [(r"図形のﾊﾟラメトリック変形を行います"[:14], RuleId.PARA_TOOLTIP), (r"範囲選択の始点をﾏ🇺🇸"[:8], RuleId.PARA_WAIT)],
    "STATE_REG": [(r"図形登録\(JWK\)を行います", RuleId.REG_TOOLTIP)],
    "STATE_DIM_ZUGEI": [(r"寸法図形にします", RuleId.DIM_ZUGEI_TOOLTIP), (r"寸法図形にする  ［寸法線］", RuleId.DIM_ZUGEI_WAIT)],
    "STATE_DIM_ZUGEI_BREAK": [(r"寸法図形を解除します", RuleId.DIM_BREAK_TOOLTIP), (r"解除する寸法図形を指示してください", RuleId.DIM_BREAK_BREAK_WAIT if hasattr(RuleId, "DIM_BREAK_BREAK_WAIT") else RuleId.DIM_BREAK_WAIT)],
    "STATE_REG_SELECT_ZU": [(r"登録選択図形を作図します", RuleId.REG_SELECT_TOOLTIP)],
    "STATE_FILE_OPEN": [(r"形式のファイルを開く", RuleId.FILE_OPEN)],
    "STATE_FILE_SAVE": [(r"形式で保存する", RuleId.FILE_SAVE)],
    "STATE_FILE_SAVE_AS": [(r"名前を付けて保存", RuleId.FILE_SAVE_AS)],
    "STATE_FILE_SAVE_OVER": [(r"上書き保存", RuleId.FILE_SAVE_OVER)],
    "STATE_FILE_OPEN_EXIST": [(r"既存のファイルを開く", RuleId.FILE_OPEN_EXIST)],
    "STATE_FILE_NEW": [(r"新規にファイルを作成", RuleId.FILE_NEW)],
    "STATE_TWO_FIVE_D_MODE": [(r"建物の高さを設定する線端部", RuleId.TWO_FIVE_D_WAIT)]
}
# ===== ✂️ utils/state_patterns.py END PART 2 ✂️ =====
