# ===== ✂️ utils/external_transform_setup.py START ✂️ =====
"""
外部変形ツール(B_MARK.BAT/A_SAVE.BAT/mark_point.ps1/dump_layers.ps1)を
JwNavigator.exeの隣に自動展開する。

👑 2026-09-11決定(DECISIONS.md参照): 「利用者がexe1個置くだけで動く状態」
を目標に、これらのファイルを手動でビルド・配置してもらう前提をやめた。
JwNavigator.exe自身にdatas(external_transform_bundle/)として埋め込み、
起動のたびに<exeのあるフォルダ>\\external_transform\\ へ展開し直す
(常にexeに同梱された最新版へ揃える)。

👑 2026-09-11さらに追記: 当初はmark_point.exe/dump_layers.exe(PyInstaller
単体ビルド)だったが、法人向けウイルス対策ソフト(ウイルスバスター
Business)が導入されたPCで、この未署名の自前exeがブロックされ
レイヤ保存が動かない事例が発生した。python.exeを追加インストールして
`python mark_point.py`形式に切り替える案も試したが、python.exeも
同様にブロックされた(署名の有無ではなく、cmd.exeからスクリプト系の
実行ファイルを子プロセスとして起動すること自体が警戒される模様)。
最終的に、Windows標準搭載で追加インストール不要な`powershell.exe`
経由に切り替えたところブロックされずに動作したため(実機確認済み、
2026-09-11)、mark_point.exe/dump_layers.exeを廃止しPowerShellスクリプト
(mark_point.ps1/dump_layers.ps1)へ全面移行した。副次的にexeバンドルが
不要になり配布サイズも小さくなった。開発環境(python main.py)は今まで
通り`mark_point.py`/`dump_layers.py`を直接使う想定で変更なし。

👑 2026-09-11追記: jw_cad側のGCOM_100キー割り付けも、当初は手動登録の
ままにしていたが「バージョンアップのたびに手でパスを直すのは面倒、
Ctrl+Jは元々JwNavigatorが送っているんだから自動でできないの？」との
要望で自動化した(ensure_gcom100_registered())。安全のため、以下の場合
だけ書き換える:
  - GCOM_100のCtrl+Jスロット(10番目のフィールド)が空 → 新規登録
  - 既に"B_MARK"が登録済みだがフォルダパスが違う → パスだけ更新
    (JwNavigator自身が以前登録したものの移設先追従とみなせるため)
それ以外(別のファイル名が既に登録されている等)は、他の用途との衝突を
避けるため一切書き換えず、ログに警告を出すだけに留める。書き換え前には
必ず`.bak_jwnavigator`のバックアップを作る(無い場合のみ、上書きしない)。
jw_cadの複数プロファイル(*.jwf/*.JWF)全部が対象。ただし`Sample.jwf`は
jw_cad自身が同梱する説明用のひな形ファイルであり実プロファイルではない
ため対象外とする。

layerdump\\(実行時のログ・トレース)は展開対象に含めない
(利用者の使用履歴なので上書きで消さない)。
"""
import glob
import os
import shutil
import sys

EXTERNAL_TRANSFORM_DIRNAME = "external_transform"
_BUNDLE_ITEMS = ("B_MARK.BAT", "A_SAVE.BAT", "mark_point.ps1", "dump_layers.ps1")

# 👑 GCOM_100は外部変形番号100〜109に対応する10ファイル分をまとめて1行に
# 書く形式(JWW_SMPL.BAT/Sample.jwf参照)。"=" の後をカンマ区切りで見た時、
# 何番目がどのCtrl+<文字>に対応するかはA=1,B=2,...J=10の並び。JwNavigator
# はCtrl+Jを使う(utils/layer_snapshot.pyのSAVE_KEY_VK)ため10番目、
# その次(11番目)がフォルダ名。実機のJw_win.jwf/kamo.JWFで実測確認済み
# (2026-09-11): "GCOM_100 =,,,,,,,,,B_MARK,C:\jww\JWW_EXT"。
_GCOM100_KEY = "GCOM_100"
_GCOM100_DIR_FIELD_INDEX = 10
_EXTERNAL_TRANSFORM_FILENAME = "B_MARK"
_SKIP_PROFILE_NAMES = {"sample.jwf"}  # jw_cad同梱のひな形、実プロファイルではない

# 👑 2026-09-14追記: 「レイヤ保存(高速)」ボタン用。GCOM_110ブロックの
# 1番目(Ctrl+K)にA_SAVEを直結登録する(GCOM_100と同じ10キー1ブロックの
# 構造、A=1番目〜J=10番目がGCOM_100、K=1番目〜T=10番目がGCOM_110、実機
# 確認済み)。B_MARKの点作図+A_SAVEへの連鎖を経由しない分、外部変形の
# 呼び出しが1回で済み体感時間が短縮できる(utils/layer_snapshot.pyの
# trigger_save_fast()参照)。安全のための制約(スロットが空でない場合は
# 書き換えない、バックアップ作成等)はGCOM_100と全く同じ。
_GCOM110_KEY = "GCOM_110"
_FAST_SAVE_FILENAME = "A_SAVE"


def _resolve_base_dir():
    # 👑 main.py/utils/palette_config.py等と同じ小さなヘルパーの重複
    # (既存パターンに合わせた許容範囲、モジュール間の不要な結合を避ける)。
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def external_transform_dir():
    return os.path.join(_resolve_base_dir(), EXTERNAL_TRANSFORM_DIRNAME)


def _bundle_source_dir():
    if not getattr(sys, "frozen", False):
        return None
    base = getattr(sys, "_MEIPASS", _resolve_base_dir())
    return os.path.join(base, "external_transform_bundle")


def ensure_deployed(log=None):
    # 👑 開発環境(python main.py)では何もしない。B_MARK.BAT/A_SAVE.BATは
    # リポジトリ直下に既にあり、mark_point.exe/dump_layers.exeは開発中は
    # 存在しない(pythonスクリプトを直接使う想定)ため、展開対象が無い。
    if not getattr(sys, "frozen", False):
        return

    source_dir = _bundle_source_dir()
    if not source_dir or not os.path.isdir(source_dir):
        if log:
            log(f"⚠️ 外部変形ツールの同梱データが見つかりません: {source_dir}")
        return

    target_dir = external_transform_dir()
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as e:
        if log:
            log(f"⚠️ 外部変形ツールの展開先フォルダを作成できません: {e}")
        return

    failed = []
    for name in _BUNDLE_ITEMS:
        src = os.path.join(source_dir, name)
        dst = os.path.join(target_dir, name)
        try:
            if os.path.isdir(src):
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy2(src, dst)
        except Exception as e:
            failed.append(name)
            if log:
                log(f"⚠️ 外部変形ツール展開失敗 ({name}): {e}")

    if log and len(failed) < len(_BUNDLE_ITEMS):
        log(f"🔧 外部変形ツールを展開しました: {target_dir}")


def ensure_gcom100_registered(jw_cad_exe_dir, log=None, reserved_letters=None):
    """jw_cadのプロファイル(*.jwf/*.JWF)全部のGCOM_100/GCOM_110を確認し、
    必要ならCtrl+J(B_MARK)/Ctrl+K(A_SAVE直結、レイヤ保存高速版用)へ
    外部変形の登録(フォルダは今のexternal_transform_dir())を行う。既に
    別用途で使われているスロットは一切書き換えない。

    👑 ensure_deployed()と同じ理由で凍結exe(sys.frozen)の時だけ動作する。
    開発環境(python main.py)ではexternal_transform_dir()がbat/exeを
    実際には展開しない場所を指すため、ここで登録するとむしろ壊れた
    パスを書いてしまう(2026-09-11、実装中に気づいて追加した安全策)。

    👑 2026-09-16追記: 戻り値は「今回どこかのプロファイルへ新規登録
    (元々空だったスロットへの初回書き込み)を行ったか」のbool。jw_cadは
    キー割り付けを自分の起動時にしか読み込まないため、jw_cadが既に
    起動済みの状態でここが新規登録を行った場合、書き込みはファイルには
    反映されるが起動中のjw_cadのメモリ上の割り付けには反映されず、
    Ctrl+J/Ctrl+Kを送っても無反応になる(実機で発覚: kosakaPCで新規
    登録直後にレイヤ保存(全自動)を実行したところ、jw_cad側の状態が
    一切変化せず「選択確定」ボタンが見つからずタイムアウトした)。
    呼び出し側(main.py)はこれを見て、利用者に「一度jw_cadを閉じて
    開き直してください」と案内する。

    👑 2026-09-16再追記: 戻り値はdict。
      new_registration: 空スロットへ初回登録した(=jw_cadの再起動が要る)
      conflicts: [(プロファイル名, "Ctrl+J"/"Ctrl+K", 既存の外部変形名)]
                 他人の登録があって書き換えを見送った箇所。放置すると
                 「レイヤ保存だけ永久に使えない」状態に無自覚で陥るため、
                 呼び出し側で利用者に知らせる。
      has_jw_win: Jw_win.jwfの有無(has_jw_win_jwf()参照)。"""
    if not jw_cad_exe_dir or not os.path.isdir(jw_cad_exe_dir):
        return {"new_registration": False, "conflicts": [], "has_jw_win": False}
    # 👑 開発環境では登録は行わないが、has_jw_winだけは正直に返す。ここで
    # 一律Falseにすると、Jw_win.jwfがあるのに「ありません」の案内が出る。
    if not getattr(sys, "frozen", False):
        return {
            "new_registration": False,
            "conflicts": [],
            "has_jw_win": has_jw_win_jwf(jw_cad_exe_dir),
        }

    target_dir = external_transform_dir()

    seen = set()
    jwf_paths = []
    for pattern in ("*.jwf", "*.JWF"):
        for p in glob.glob(os.path.join(jw_cad_exe_dir, pattern)):
            key = os.path.normcase(os.path.abspath(p))
            if key not in seen:
                seen.add(key)
                jwf_paths.append(p)

    # 👑 2026-09-16: jw_cadは設定の大半をレジストリ
    # (HKCU\Software\Jw_cad\jw_win)に保存しているが、**GCOM_1XX(Ctrl+英字
    # での外部変形起動)だけはレジストリに一切保存されない**(実機のレジストリ
    # を全走査して確認。KEY割り付けは`KeyCom`キーにあるのにGCOMは無く、
    # あるのは「最後に使った外部変形ファイル」等の履歴パスだけだった)。
    # GCOMはjw_cadが**起動時にJw_win.jwfから読む**ときにしかメモリへ載らない。
    # そのためJw_win.jwfが無い環境では、kousaka.JWFのような名前付き
    # プロファイルへいくら登録しても、明示的に読み込まない限り永久に
    # Ctrl+J/Ctrl+Kが効かない(kosakaPCがこの状態で、9/11から一度も
    # レイヤ保存が成功していなかった)。無言では気づけないので警告する。
    if not any(os.path.basename(p).lower() == "jw_win.jwf" for p in jwf_paths):
        if log:
            log(
                "⚠️ jw_cadのフォルダにJw_win.jwfがありません。"
                "jw_cadは起動時にこのファイルからしか外部変形のキー割り付けを"
                "読まないため、このままではレイヤ保存が動きません。"
                "jw_cadの[設定]→[環境設定ファイル]→[書込み]でJw_win.jwfを"
                "作成してください。"
            )

    did_new_registration = False
    conflicts = []
    keys = {_EXTERNAL_TRANSFORM_FILENAME: None, _FAST_SAVE_FILENAME: None}
    for jwf_path in jwf_paths:
        if os.path.basename(jwf_path).lower() in _SKIP_PROFILE_NAMES:
            continue
        result = _register_in_profile(
            jwf_path, target_dir, log=log, reserved_letters=reserved_letters
        )
        if result["new_registration"]:
            did_new_registration = True
        conflicts.extend(result["conflicts"])
        # 👑 実際に送るキーはjw_cadが起動時に読むJw_win.jwfの登録が正。
        # 他のプロファイルは明示的に読み込まない限り効かないため
        # (jwnavigator_jwcad_settings_architecture参照)。
        if os.path.basename(jwf_path).lower() == "jw_win.jwf":
            keys = result["keys"]

    return {
        "new_registration": did_new_registration,
        "conflicts": conflicts,
        "has_jw_win": has_jw_win_jwf(jw_cad_exe_dir),
        "save_key_letter": keys.get(_EXTERNAL_TRANSFORM_FILENAME),
        "fast_save_key_letter": keys.get(_FAST_SAVE_FILENAME),
    }


# 👑 GCOM_100の0〜9番目がCtrl+A〜Ctrl+J、GCOM_110の0〜9番目がCtrl+K〜Ctrl+T
# (実機確認済み)。この並びから「スロット位置 → 送るべきキー」が一意に決まる。
_GCOM_BLOCK_KEYS = (_GCOM100_KEY, _GCOM110_KEY)
_SLOTS_PER_BLOCK = 10
_DIR_FIELD_INDEX = 10
_MIN_FIELDS = 11
# 既定の割り当て(従来と同じ): B_MARK=Ctrl+J、A_SAVE=Ctrl+K
_PREFERRED_SLOT = {
    _EXTERNAL_TRANSFORM_FILENAME: (0, 9),   # GCOM_100の10番目 = Ctrl+J
    _FAST_SAVE_FILENAME: (1, 0),            # GCOM_110の1番目  = Ctrl+K
}


def _slot_key_letter(block_index, slot_index):
    return chr(ord("A") + block_index * _SLOTS_PER_BLOCK + slot_index)


def _slot_of_letter(letter):
    index = ord(letter) - ord("A")
    return index // _SLOTS_PER_BLOCK, index % _SLOTS_PER_BLOCK


# 👑 2026-09-16: 既定のCtrl+J/Ctrl+Kが埋まっていた時に代わりを探す順番。
# アルファベット順(A,B,C…)だと左手の狭い範囲に集中してしまい、Ctrlを
# 押しながらだと押しづらい上に、定番ショートカットとも近い。kamoの指示
# 「BDEは後回しに。キーボードの右のほうから使いましょう」に従い、
# QWERTY配列で**右側にあるキーから順**に並べてある(同じくらいの位置なら
# ホームポジション行を優先)。使えるのはGCOM_100=A〜J、GCOM_110=K〜Tの
# 20文字だけなので、その20文字をすべて1回ずつ並べている。
# 実際にはこの順から「jw_cadが使用中のキー」を除外して使う。
_FALLBACK_LETTER_ORDER = "PLOKIMJNHTGBFREDCSQA"


def _register_in_profile(jwf_path, target_dir, log=None, reserved_letters=None):
    """1つのプロファイルにB_MARK/A_SAVEを登録する。

    👑 2026-09-16: 以前は「Ctrl+Jが埋まっていたら諦める」だけだった。
    しかしJwNavigatorが送るキーは`utils/layer_snapshot.py`にハードコード
    されていたため、利用者が別のスロットへ手動登録しても**JwNavigatorは
    Ctrl+J/Ctrl+Kを送り続け、結局動かなかった**(案内文も「空いている
    スロットへ手動登録を」と誤った手順を書いていた)。
    ここでは既定のスロットが埋まっていたら**空いているスロットを自動で
    探して登録し、実際に使ったキーを呼び出し側へ返す**。呼び出し側は
    そのキーをlayer_snapshotへ渡すので、どのスロットに入っても動く。

    戻り値: {"keys": {"B_MARK": "J"等 or None, "A_SAVE": ...},
             "new_registration": bool,
             "conflicts": [(プロファイル名, 説明, 既存の外部変形名)]}"""
    name = os.path.basename(jwf_path)
    empty = {"keys": {_EXTERNAL_TRANSFORM_FILENAME: None, _FAST_SAVE_FILENAME: None},
             "new_registration": False, "conflicts": []}
    try:
        raw = open(jwf_path, "rb").read()
    except Exception as e:
        if log:
            log(f"⚠️ {name}の読み込みに失敗したため外部変形の登録をスキップしました: {e}")
        return empty

    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(newline)

    # ブロックごとに (linesの行番号, 行頭"GCOM_1X0 ", フィールド配列) を用意する
    blocks = {}
    for block_index, gcom_key in enumerate(_GCOM_BLOCK_KEYS):
        key_bytes = gcom_key.encode("ascii")
        for i, line_bytes in enumerate(lines):
            if not line_bytes.startswith(key_bytes) or b"=" not in line_bytes:
                continue
            try:
                line_text = line_bytes.decode("cp932")
            except UnicodeDecodeError:
                if log:
                    log(f"⚠️ {name}の{gcom_key}行の文字コードが想定と違うため、自動登録をスキップしました。")
                break
            prefix, _, rest = line_text.partition("=")
            fields = rest.split(",")
            while len(fields) < _MIN_FIELDS:
                fields.append("")
            blocks[block_index] = {"line": i, "prefix": prefix, "fields": fields}
            break
        else:
            if log:
                log(
                    f"⚠️ {name}に{gcom_key}の行がありません。"
                    "このプロファイルにはその範囲のキーを登録できませんでした。"
                )

    if not blocks:
        return empty

    result = dict(empty)
    result["keys"] = dict(empty["keys"])
    changed = False

    for filename in (_EXTERNAL_TRANSFORM_FILENAME, _FAST_SAVE_FILENAME):
        # 1) 既に登録済みならその場所を使う(フォルダだけ今の展開先へ追従)
        found_at = None
        for block_index, block in blocks.items():
            for slot in range(_SLOTS_PER_BLOCK):
                if block["fields"][slot].strip() == filename:
                    found_at = (block_index, slot)
                    break
            if found_at:
                break
        if found_at:
            block = blocks[found_at[0]]
            letter = _slot_key_letter(*found_at)
            if block["fields"][_DIR_FIELD_INDEX].strip() != target_dir:
                block["fields"][_DIR_FIELD_INDEX] = target_dir
                changed = True
                if log:
                    log(f"🔧 {name}の{filename}(Ctrl+{letter})の登録先を更新しました: {target_dir}")
            elif log:
                log(f"✅ {name}の{filename}はCtrl+{letter}に登録済みです: {target_dir}")
            result["keys"][filename] = letter
            continue

        # 2) 既定のスロット → 空いていれば使う。埋まっていれば他の空きを探す
        # 👑 2026-09-16: 空きを探す際、jw_cadが既にCtrl+英字で使っている
        # キー(Ctrl+C/N/O/P/S等。呼び出し側がメニューから実測して渡す)は
        # 避ける。奪うとその人の普段の操作が変わってしまうため
        # (kamoの指摘「Ctrl+Aとかターゲットが違ったら違う話になります」)。
        # 避けた結果どこにも入らない場合は、勝手に奪わずconflictとして
        # 利用者に知らせる。
        reserved = {c.upper() for c in (reserved_letters or ())}
        candidates = [_PREFERRED_SLOT[filename]]
        for letter in _FALLBACK_LETTER_ORDER:
            slot = _slot_of_letter(letter)
            if slot not in candidates:
                candidates.append(slot)
        candidates = [
            c for c in candidates if _slot_key_letter(*c) not in reserved
        ]
        placed = None
        for block_index, slot in candidates:
            block = blocks.get(block_index)
            if block is None:
                continue
            if block["fields"][slot].strip() == "":
                block["fields"][slot] = filename
                block["fields"][_DIR_FIELD_INDEX] = target_dir
                placed = (block_index, slot)
                break
        if placed:
            letter = _slot_key_letter(*placed)
            changed = True
            result["new_registration"] = True
            result["keys"][filename] = letter
            if log:
                pref = _slot_key_letter(*_PREFERRED_SLOT[filename])
                note = "" if letter == pref else f"(既定のCtrl+{pref}は使用中だったため)"
                log(f"🔧 {name}の{filename}をCtrl+{letter}に新規登録しました{note}: {target_dir}")
        else:
            occupant = ""
            pb, ps = _PREFERRED_SLOT[filename]
            if pb in blocks:
                occupant = blocks[pb]["fields"][ps].strip()
            letter = _slot_key_letter(pb, ps)
            result["conflicts"].append((name, f"Ctrl+{letter}", occupant or "不明"))
            if log:
                log(
                    f"⚠️ {name}に{filename}を登録できる空きキーがありません"
                    f"(既定のCtrl+{letter}は「{occupant}」が使用中)。"
                    "レイヤ保存を使うには、jw_cad側でどれか1つ割り当てを外してください。"
                )

    if not changed:
        return result

    for block in blocks.values():
        new_line = block["prefix"] + "=" + ",".join(block["fields"])
        lines[block["line"]] = new_line.encode("cp932")
    try:
        backup_path = jwf_path + ".bak_jwnavigator"
        if not os.path.exists(backup_path):
            shutil.copy2(jwf_path, backup_path)
        with open(jwf_path, "wb") as f:
            f.write(newline.join(lines))
    except Exception as e:
        if log:
            log(f"⚠️ {name}への書き込みに失敗しました: {e}")
        result["new_registration"] = False
    return result


def has_jw_win_jwf(jw_cad_exe_dir):
    """👑 2026-09-16: jw_cadが起動時に読む唯一のファイルJw_win.jwfがあるか。
    GCOM(Ctrl+英字での外部変形起動)はレジストリに保存されず、このファイル
    からしか読み込まれないことを実機の対照実験で確認済み(GCOM_110行を空に
    して再起動するとCtrl+Kが完全に無反応になり、戻すとまた効く)。
    無い場合は登録しても永久に効かないため、呼び出し側(main.py)は
    「利用者が後からJw_win.jwfを作った」ケースを拾えるよう、確認済み
    フラグを立てずに次回のjw_cad検出でもう一度確認する。"""
    if not jw_cad_exe_dir or not os.path.isdir(jw_cad_exe_dir):
        return False
    return os.path.isfile(os.path.join(jw_cad_exe_dir, "Jw_win.jwf"))


def _log_registered_dir_contents(line_text, gcom_key, log):
    """GCOM_1XX行の11番目(フォルダ)を取り出し、そこに実際の.BATがあるかを見る。
    jw_cadが本当に見に行くのはこのフォルダなので、展開先(external_transform_dir)
    が正しくても、ここがズレていればレイヤ保存は動かない。"""
    fields = line_text.partition("=")[2].split(",")
    if len(fields) <= _GCOM100_DIR_FIELD_INDEX:
        return
    registered_dir = fields[_GCOM100_DIR_FIELD_INDEX].strip()
    if not registered_dir:
        log(f"🔎 [環境]     → {gcom_key}の登録先フォルダが空です")
        return
    filename = (
        _EXTERNAL_TRANSFORM_FILENAME if gcom_key == _GCOM100_KEY else _FAST_SAVE_FILENAME
    ) + ".BAT"
    path = os.path.join(registered_dir, filename)
    if os.path.isfile(path):
        log(f"🔎 [環境]     → 登録先に{filename}あり: {registered_dir}")
    else:
        log(f"🔎 [環境]     → ❌ 登録先に{filename}がありません: {registered_dir}")


def describe_environment(jw_cad_exe_dir, log=None):
    """👑 2026-09-16: 他人のPC(kosakaPC等)は頻繁に触れないため、「1回起動して
    ログを送ってもらえば原因が確定する」ことを狙った環境スナップショット。
    レイヤ保存が動かない時に必要な情報(外部変形ファイルの実在、jw_cadの
    プロファイル構成、GCOM行の実際の中身)を起動直後にまとめて吐く。

    実際にkosakaPCの調査では、この情報が無いために
    「Jw_win.jwfが無い」という一点に辿り着くまで往復を繰り返した。"""
    if not log:
        return

    target_dir = external_transform_dir()
    log(f"🔎 [環境] 外部変形フォルダ: {target_dir}")
    for name in _BUNDLE_ITEMS:
        path = os.path.join(target_dir, name)
        try:
            size = os.path.getsize(path)
            log(f"🔎 [環境]   {name}: あり ({size} bytes)")
        except OSError:
            log(f"🔎 [環境]   {name}: ❌ ありません")

    log(f"🔎 [環境] jw_cadフォルダ: {jw_cad_exe_dir}")
    if not jw_cad_exe_dir or not os.path.isdir(jw_cad_exe_dir):
        log("🔎 [環境]   ❌ フォルダを特定できませんでした")
        return

    seen = set()
    jwf_paths = []
    for pattern in ("*.jwf", "*.JWF"):
        for p in glob.glob(os.path.join(jw_cad_exe_dir, pattern)):
            key = os.path.normcase(os.path.abspath(p))
            if key not in seen:
                seen.add(key)
                jwf_paths.append(p)
    if not jwf_paths:
        log("🔎 [環境]   ❌ プロファイル(*.jwf/*.JWF)が1つもありません")
        return

    has_jw_win = any(os.path.basename(p).lower() == "jw_win.jwf" for p in jwf_paths)
    log(f"🔎 [環境]   Jw_win.jwf(jw_cadが起動時に読む唯一のファイル): "
        f"{'あり' if has_jw_win else '❌ ありません'}")
    for jwf_path in jwf_paths:
        name = os.path.basename(jwf_path)
        if name.lower() in _SKIP_PROFILE_NAMES:
            continue
        try:
            raw = open(jwf_path, "rb").read()
        except Exception as e:
            log(f"🔎 [環境]   {name}: 読み取り失敗 {e}")
            continue
        newline = b"\r\n" if b"\r\n" in raw else b"\n"
        found = {}
        for line_bytes in raw.split(newline):
            for key in (_GCOM100_KEY, _GCOM110_KEY):
                if line_bytes.startswith(key.encode("ascii")):
                    found[key] = line_bytes.decode("cp932", errors="replace").rstrip()
        for key in (_GCOM100_KEY, _GCOM110_KEY):
            line_text = found.get(key)
            if line_text is None:
                log(f"🔎 [環境]   {name}: ❌ {key}の行がありません")
                continue
            log(f"🔎 [環境]   {name}: {line_text}")
            # 👑 DECISIONS.md(2026-09-14)の教訓: 「外部変形が絡む不具合を追う
            # 前に、まずGCOM_1XXが指すフォルダにA_SAVE.BAT/B_MARK.BATが実在
            # するかを確認すること」。展開先(external_transform_dir())と
            # jw_cadが実際に見に行く登録先はズレることがある(リビルド後、
            # exeの置き場所を変えた後など)ので、登録先の方を確認する。
            _log_registered_dir_contents(line_text, key, log)


# ===== ✂️ utils/external_transform_setup.py END ✂️ =====
