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
    SOLID_TOOLTIP = auto()
    TWO_FIVE_D_TOOLTIP = auto()
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
    COPY_WAIT = auto()
    MOVE_WAIT = auto()
    POLYGON_WAIT = auto()
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
    SETSUEN_WAIT_3RD = auto()
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
    # 👑 2026-08-19実測で新規追加（マウスオン全85コマンド走査で判明した、
    # ツールチップ未登録だったコマンド分）。すべてツールチップ文言のみで、
    # 実測データに存在しない補助状態（WAIT）は推測で追加していない。
    MODORU_TOOLTIP = auto()
    SUSUMU_TOOLTIP = auto()
    BLOCK_KA_TOOLTIP = auto()
    BLOCK_KAI_TOOLTIP = auto()
    BLOCK_ZOKUSEI_TOOLTIP = auto()
    BLOCK_HEN_TOOLTIP = auto()
    BLOCK_SHU_TOOLTIP = auto()
    KIRITORI_TOOLTIP = auto()
    CLIP_COPY_TOOLTIP = auto()
    HARITSUKE_TOOLTIP = auto()
    SEN_ZOKUSEI_TOOLTIP = auto()
    ZOKUSEI_SHUTOKU_TOOLTIP = auto()
    SEN_KAKUDO_TOOLTIP = auto()
    ENCHOKU_KAKU_TOOLTIP = auto()
    X_JIKU_KAKU_TOOLTIP = auto()
    NITEN_KAKU_TOOLTIP = auto()
    SEN_CHO_TOOLTIP = auto()
    NITEN_CHO_TOOLTIP = auto()
    KANKAKU_TOOLTIP = auto()
    KIHON_SETTEI_TOOLTIP = auto()
    PRINT_TOOLTIP = auto()
    TAG_JUMP_TOOLTIP = auto()
    CHUSHIN_TEN_TOOLTIP = auto()
    SENJO_TEN_TOOLTIP = auto()
    ENSHU_4TEN_TOOLTIP = auto()
    HIKAGEZU_TOOLTIP = auto()
    TENKUZU_TOOLTIP = auto()
# ===== ✂️ utils/state_patterns.py END PART 1 ✂️ =====

# ===== ✂️ utils/state_patterns.py START PART 2 ✂️ =====
STATE_DATABASE = {
    "STATE_LINE": [(r"線を書きます", RuleId.LINE_TOOLTIP), (r"始点を指示してください", RuleId.LINE_WAIT)],
    # 👑 RECT_WAIT実測メモ（2026-08-25収集）: ツールバーから矩形を選択した
    # 直後の文言はSTATE_LINEの「始点を指示してください」と完全に同一
    # （実測で確認）。旧パターン「矩形の基準点を指示して下さい」がいつ
    # 出るのかは未確認だが、消さずに残しておく（誤りだった場合も実害はない）。
    "STATE_RECT": [
        (r"矩形を書きます", RuleId.RECT_TOOLTIP),
        (r"矩形の基準点を指示して下さい", RuleId.RECT_WAIT),
        (r"始点を指示してください", RuleId.RECT_WAIT),
    ],
    "STATE_CIRCLE": [(r"円を書く", RuleId.CIRCLE_TOOLTIP), (r"中心点を指示してください", RuleId.CIRCLE_WAIT)],
    "STATE_TEXT": [(r"文字を書きます", RuleId.TEXT_TOOLTIP), (r"文字を入力するか", RuleId.TEXT_WAIT)],
    "STATE_DIM": [(r"寸法を記入します", RuleId.DIM_TOOLTIP), (r"\[寸法\]", RuleId.DIM_BRACKET), (r"寸法線の位置を指示して下さい", RuleId.DIM_WAIT)],
    "STATE_TWO_LINE": [(r"２線を作図します", RuleId.TWO_LINE_TOOLTIP), (r"基準線を指示してください", RuleId.TWO_LINE_WAIT)],
    # 👑 CENTER_WAIT実測メモ（2026-08-19収集）: 実際の文言は
    # "１番目の線・円をﾏｳｽ(L)で、読取点をﾏｳｽ(R)で指示してください。" だが、
    # この文言はSTATE_SETSUEN（接円）の1〜2番目指示と完全に同一で衝突するため、
    # 誤判定を避けるためあえて登録しない。区別できるのはSTATE_SETSUEN側の
    # 「３番目」の文言が出た場合のみ（接円は3つ必要、中心線は2つで確定するため）。
    "STATE_CENTER": [(r"中心線を作図します", RuleId.CENTER_TOOLTIP)],
    "STATE_RENTENT": [(r"連続線・連続円弧を作図します", RuleId.RENTENT_TOOLTIP)],
    "STATE_AUTO": [(r"AUTOモードを実行します", RuleId.AUTO_TOOLTIP), (r"AUTOモード   \(L\)free", RuleId.AUTO_WAIT)],
    "STATE_POINT": [(r"点を書きます", RuleId.POINT_TOOLTIP), (r"点位置を指示してください", RuleId.POINT_WAIT)],
    "STATE_SESSEN": [(r"接線を作図します", RuleId.SESSEN_TOOLTIP), (r"円を指示してください", RuleId.SESSEN_WAIT)],
    # 👑 SETSUEN実測メモ（2026-08-19収集）: 1〜2番目の指示文言はSTATE_CENTERと
    # 完全に同一で衝突するため未登録。「３番目」はSTATE_CENTERに存在しない
    # （接円は円3つが必要、中心線は2つで確定するため）唯一の区別可能な文言。
    "STATE_SETSUEN": [
        (r"接円を作図します", RuleId.SETSUEN_TOOLTIP),
        (r"３番目の線・円をﾏｳｽ", RuleId.SETSUEN_WAIT_3RD),
    ],
    "STATE_HATCH": [
        (r"ハッチングを行います", RuleId.HATCH_TOOLTIP),
        (r"始めの線・弧をﾏｳｽ\(L\)で、閉鎖連続線・円をﾏｳｽ\(R\)で指示してください", RuleId.HATCH_WAIT),
    ],
    "STATE_TATEG": [(r"建具を選択してください", RuleId.TATEG_WAIT), (r"ﾊﾟラメトリックな建具", RuleId.TATEG_TOOLTIP)],
    # 👑 POLYGON実測メモ（2026-08-26収集）: 多角形も中心点から描き始める
    # 仕様のため、最初の入力待ち文言がSTATE_CIRCLE（円弧）の
    # 「中心点を指示してください」と完全に同一（実測確認）。線↔矩形と
    # 同じ衝突なので、直前に確定していたツールチップで区別する。
    "STATE_POLYGON": [(r"多角形（２辺）を作図します", RuleId.POLYGON_TOOLTIP), (r"中心点を指示してください", RuleId.POLYGON_WAIT)],
    "STATE_CURVE": [(r"曲線を作図します", RuleId.CURVE_TOOLTIP)],
    # 👑 SOLID実測メモ（2026-08-26収集）: 対応する状態が一つも登録されて
    # おらず、多角形など直前のツールチップに誤って推定されていた
    # （INFERRED_WAIT機構の実測で発覚）。ツールチップを登録して解決。
    "STATE_SOLID": [(r"ソリッドを作図します", RuleId.SOLID_TOOLTIP)],
    "STATE_RANGE": [(r"範囲を指定し", RuleId.RANGE_TOOLTIP), (r"範囲選択の始点を", RuleId.RANGE_WAIT)],
    "STATE_FUKUSEN": [(r"元の線に平行な線をつくります", RuleId.FUKUSEN_TOOLTIP), (r"複線にする図形を選択", RuleId.FUKUSEN_WAIT)],
    # 👑 このWAIT文言「線（Ａ）指示(L)　　　　線切断(R)」はSTATE_CHAMFER（面取）と
    # 完全に同一（2026-08-19実測確認）。ツールチップは別なので初回検知は問題ないが、
    # 一度この状態に入るとコーナー/面取の区別はステータスバー文言だけでは不可能。
    "STATE_CORNER": [(r"２線のコーナー処理を行います", RuleId.CORNER_TOOLTIP), (r"線（Ａ）指示", RuleId.CORNER_WAIT)],
    "STATE_EXTEND": [(r"線を伸縮します", RuleId.EXTEND_TOOLTIP), (r"指示点までの伸縮線", RuleId.EXTEND_WAIT)],
    # 👑 CHAMFER/CORNER衝突メモ（2026-08-19実測）: 面取のWAIT文言は
    # 「線（Ａ）指示(L)　　　　線切断(R)」で、これはCORNER（コーナー）の
    # WAIT文言と完全に同一（実測で確認済み）。旧パターン「面取する１番目の線」
    # 「線切断（Ｒ）」（全角括弧）は一度も実測されておらず、実際の文言
    # （半角括弧）と一致しない誤ったパターンだったため削除した。
    "STATE_CHAMFER": [(r"２線を面取りします", RuleId.CHAMFER_TOOLTIP)],
    "STATE_DELETE": [(r"図形を消去します", RuleId.DELETE_TOOLTIP), (r"線・円マウス\(L\)部分消し", RuleId.DELETE_WAIT)],
    # 👑 COPY/MOVE実測メモ（2026-08-26収集）: 複写・移動はどちらも、対象を
    # 選ぶ最初のフェーズでSTATE_RANGE（範囲選択）と完全に同一の文言
    # 「範囲選択の始点を...」を経由する（jw_cad側の仕様として、複写・移動
    # の対象選択が範囲選択と同じUIフローになっているため）。線↔矩形と
    # 同じ衝突なので、直前に確定していたツールチップで区別する。
    "STATE_COPY": [(r"図形を複写します", RuleId.COPY_TOOLTIP), (r"範囲選択の始点を", RuleId.COPY_WAIT)],
    "STATE_MOVE": [(r"図形を移動します", RuleId.MOVE_TOOLTIP), (r"範囲選択の始点を", RuleId.MOVE_WAIT)],
    "STATE_IMAGE": [(r"画像の挿入、サイズ調整", RuleId.IMAGE_TOOLTIP)],
    "STATE_HOURAKU": [(r"図形の外郭線をつなげて整理します", RuleId.HOURAKU_TOOLTIP), (r"包絡範囲の始点指示", RuleId.HOURAKU_WAIT)],
    # 👑 BUNKATSU_WAIT実測メモ（2026-08-26収集）: 「線・円（Ａ）指示 ﾏｳｽ(L)
    # 　分割始点指示 ﾏｳｽ(R)　連続点分割 (RR)」が実際のWAIT文言。
    "STATE_BUNKATSU": [
        (r"点や線の間を分割します", RuleId.BUNKATSU_TOOLTIP),
        (r"分割始点指示", RuleId.BUNKATSU_WAIT),
    ],
    "STATE_CLEANUP": [(r"データの整理をします", RuleId.CLEANUP_TOOLTIP)],
    "STATE_ATTRIB": [(r"データの属性を変更します", RuleId.ATTRIB_TOOLTIP), (r"変更するデータを指示してください", RuleId.ATTRIB_WAIT)],
    "STATE_ZUGEI": [(r"図形ファイルを読み込みます", RuleId.ZUGEI_TOOLTIP)],
    "STATE_KIGOU": [(r"線記号変形を行います", RuleId.KIGOU_TOOLTIP), (r"記号を選択してください", RuleId.KIGOU_WAIT)],
    # 👑 COORD/SHIKI衝突メモ（2026-08-19実測）: 座標(COORD)と式計算(SHIKI)は、
    # どちらも自コマンドのツールチップの直後に全く同じ文言
    # "□□　　　項目を選択してください　　　□□" を表示する（汚染データではなく
    # Jw_cad側の実仕様として確認済み）。現状はSHIKI側の正規表現の方が長いため
    # ソート順で先にマッチし、実際にはCOORDが呼ばれていてもSHIKIと誤判定される。
    # ステータスバー文言だけでは区別不可能。区別が必要になったら、直前に押した
    # ボタン（インテントロック）などステータスバー以外の情報を併用すること。
    "STATE_COORD": [(r"座標ファイルの読込・書込", RuleId.COORD_TOOLTIP), (r"項目を選択してください", RuleId.COORD_WAIT)],
    "STATE_GAIBU": [(r"外部変形を行います", RuleId.GAIBU_TOOLTIP)],
    "STATE_SOKUTEI": [(r"距離・面積・座標・角度を測定", RuleId.SOKUTEI_TOOLTIP)],
    "STATE_HYOU": [(r"表計算を行います", RuleId.HYOU_TOOLTIP)],  # HYOU_WAIT: 未実測のため削除（実測後に追加。旧パターンはSTATE_RANGEの文言の誤コピーだった）
    # 👑 DIST_WAIT実測メモ（2026-08-26収集）: 旧パターン「始点を指示して
    # ください  (L)free」は、線・矩形・円弧等と共通の汎用「点を指示」文言
    # の先頭部分に過ぎず、距離指定点に固有ではなかった（括弧削除処理の
    # バグで末尾の"(L)free"が常に消えていたため、これまで表面化していな
    # かった）。距離指定点は現在パレット未設定のため、実害を避けるため
    # WAITパターンは削除し、固有のツールチップのみ残す。
    "STATE_DIST": [(r"始点からの距離を指定して点", RuleId.DIST_TOOLTIP)],
    "STATE_SHIKI": [(r"式計算を行います", RuleId.SHIKI_TOOLTIP), (r"□□　　　項目を選択してください", RuleId.SHIKI_WAIT)],
    # 👑 PARA実測メモ（2026-08-26収集）: 旧パターンは全角カタカナ「ラ」を
    # 含んでいたが、実際の文言は半角カタカナ「ﾊﾟﾗﾒﾄﾘｯｸ」だったため一度も
    # 一致していなかった（INFERRED_WAIT機構の実測で発覚。直前のツールチップ
    # に誤って推定され続けていた）。実測値に修正。
    "STATE_PARA": [(r"図形のﾊﾟﾗﾒﾄﾘｯｸ変形を行います", RuleId.PARA_TOOLTIP)],  # PARA_WAIT: 未実測のため削除（旧パターンはSTATE_RANGEの文言の誤コピーだった）
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
    # 👑 2026-08-19実測で判明: このパターンは元々2.5D用のつもりだったが、実際の
    # 2.5D文言は「高さ・奥行を設定する線端部または円を指示」であり、
    # 「建物の高さを設定する線端部を指示してください」は日影図・天空図の文言
    # だった（天空図は自身のツールチップで「日影図のデータを使用して」と明言
    # しており、意図的に同じ高さ設定データを共有している）。日影図・天空図は
    # まだ専用のSTATEを持たないため、判定を壊さないよう文言を実測値に訂正する
    # にとどめる。日影図/天空図を区別したくなったら、2段階目の固有文言
    # （天空図: 「正射影　測定点を指示してください。」「天空図の作図位置（円中心）
    # を指示してください。」）を使うこと。
    # 👑 2.5Dのツールチップ実測メモ（2026-08-26収集）:
    # 「２．５Dのデータ入力と作図をします。」。
    "STATE_TWO_FIVE_D_MODE": [
        (r"２．５Dのデータ入力と作図をします", RuleId.TWO_FIVE_D_TOOLTIP),
        (r"高さ・奥行を設定する線端部または円を指示", RuleId.TWO_FIVE_D_WAIT),
    ],
    # 👑 2026-08-19実測追加分（全85コマンドのマウスオン走査で判明。
    # ツールチップのみ、実測されたWAIT文言のみを採用）。
    "STATE_MODORU": [(r"直前に行った動作を元に戻す", RuleId.MODORU_TOOLTIP)],
    "STATE_SUSUMU": [(r"直前に行った動作を繰り返す", RuleId.SUSUMU_TOOLTIP)],
    "STATE_BLOCK_KA": [(r"選択されたデータをブロック化します", RuleId.BLOCK_KA_TOOLTIP)],
    "STATE_BLOCK_KAI": [(r"選択されたデータのブロックを解除します", RuleId.BLOCK_KAI_TOOLTIP)],
    "STATE_BLOCK_ZOKUSEI": [(r"ブロックデータのレイヤ属性を変更します", RuleId.BLOCK_ZOKUSEI_TOOLTIP)],
    # 👑 BL編/BL終は文字列として排他（「編集作業をします」と「編集作業を終了します」）。
    "STATE_BLOCK_HEN": [(r"ブロック要素の編集作業をします", RuleId.BLOCK_HEN_TOOLTIP)],
    "STATE_BLOCK_SHU": [(r"ブロック要素の編集作業を終了します", RuleId.BLOCK_SHU_TOOLTIP)],
    "STATE_KIRITORI": [(r"選択範囲を切り取ってクリップボードに保存", RuleId.KIRITORI_TOOLTIP)],
    "STATE_CLIP_COPY": [(r"選択範囲をコピーしてクリップボードに保存", RuleId.CLIP_COPY_TOOLTIP)],
    "STATE_HARITSUKE": [(r"クリップボードの内容を貼り付け", RuleId.HARITSUKE_TOOLTIP)],
    "STATE_SEN_ZOKUSEI": [(r"線属性の設定を行います", RuleId.SEN_ZOKUSEI_TOOLTIP)],
    "STATE_ZOKUSEI_SHUTOKU": [(r"属性取得を行います。", RuleId.ZOKUSEI_SHUTOKU_TOOLTIP)],
    "STATE_SEN_KAKUDO": [(r"線角度取得を行います。", RuleId.SEN_KAKUDO_TOOLTIP)],
    "STATE_ENCHOKU_KAKU": [(r"線鉛直角度取得を行います。", RuleId.ENCHOKU_KAKU_TOOLTIP)],
    "STATE_X_JIKU_KAKU": [(r"X軸角度取得を行います。", RuleId.X_JIKU_KAKU_TOOLTIP)],
    "STATE_NITEN_KAKU": [(r"２点間角度取得を行います。", RuleId.NITEN_KAKU_TOOLTIP)],
    "STATE_SEN_CHO": [(r"線の長さを取得します。", RuleId.SEN_CHO_TOOLTIP)],
    "STATE_NITEN_CHO": [(r"２点間の長さを取得します。", RuleId.NITEN_CHO_TOOLTIP)],
    "STATE_KANKAKU": [(r"線･円と線・円・点の間隔を取得します。", RuleId.KANKAKU_TOOLTIP)],
    "STATE_KIHON_SETTEI": [(r"基本的な操作・色彩等を設定します。", RuleId.KIHON_SETTEI_TOOLTIP)],
    "STATE_PRINT": [(r"作業中のファイルを印刷", RuleId.PRINT_TOOLTIP)],
    "STATE_TAG_JUMP": [(r"のファイルへタグｼﾞｬﾝﾌﾟする", RuleId.TAG_JUMP_TOOLTIP)],
    "STATE_CHUSHIN_TEN": [(r"線・円中心または２点間の中心を取得します。", RuleId.CHUSHIN_TEN_TOOLTIP)],
    "STATE_SENJO_TEN": [(r"線上点・交点を取得します。", RuleId.SENJO_TEN_TOOLTIP)],
    "STATE_ENSHU_4TEN": [(r"円周1/4点を取得します。", RuleId.ENSHU_4TEN_TOOLTIP)],
    # 👑 日影図/天空図はWAIT文言が完全一致で衝突するため（STATE_TWO_FIVE_D_MODEの
    # コメント参照）、ツールチップのみで登録する。
    "STATE_HIKAGEZU": [(r"日影図のデータ入力と日影図を作成します。", RuleId.HIKAGEZU_TOOLTIP)],
    "STATE_TENKUZU": [(r"日影図のデータを使用して天空図を作成します。", RuleId.TENKUZU_TOOLTIP)],
}

# 👑 マウスを乗せただけ（クリックせず）でもツールチップ文言はステータスバーに
# 出てしまうため、「実際にコマンドを開始しないと出ない」文言（＝WAIT系ルール）
# を持つ状態は、そちらが出るまではパレット側への反映を待つ、という判定に使う。
# ファイル系の一発文言（FILE_OPEN/FILE_SAVE等）とDIM_BRACKETはツールバーの
# マウスオンでは出ない（ダイアログ操作起点の文言）ため、非ホバー扱いに含める。
# 👑 SETSUEN_WAIT_3RDは名前が「_WAIT」で終わっていない（「_3RD」で終わる）
# ため、is_hover_trustworthy_ruleの素朴な終端チェックだけでは拾えず、接円
# だけホバー扱いされてしまうバグがあった（実測で発覚）。ここに明示追加する。
NON_HOVER_ONLY_RULE_NAMES = {
    "FILE_OPEN", "FILE_SAVE", "FILE_SAVE_AS", "FILE_SAVE_OVER", "FILE_OPEN_EXIST", "FILE_NEW",
    "DIM_BRACKET", "SETSUEN_WAIT_3RD",
}

STATES_WITH_WAIT_RULE = {
    state_id
    for state_id, rule_tuples in STATE_DATABASE.items()
    if any(
        rule_enum.name.endswith("_WAIT") or rule_enum.name in NON_HOVER_ONLY_RULE_NAMES
        for _, rule_enum in rule_tuples
    )
}


def is_hover_trustworthy_rule(rule_name: str) -> bool:
    return rule_name.endswith("_WAIT") or rule_name in NON_HOVER_ONLY_RULE_NAMES
# ===== ✂️ utils/state_patterns.py END PART 2 ✂️ =====
