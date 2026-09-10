# ===== ✂️ utils/external_transform_setup.py START ✂️ =====
"""
外部変形ツール(B_MARK.BAT/A_SAVE.BAT/mark_point.exe/dump_layers.exe)を
JwNavigator.exeの隣に自動展開する。

👑 2026-09-11決定(DECISIONS.md参照): 「利用者がexe1個置くだけで動く状態」
を目標に、これらのファイルを手動でビルド・配置してもらう前提をやめた。
JwNavigator.exe自身にdatas(external_transform_bundle/)として埋め込み、
起動のたびに<exeのあるフォルダ>\\external_transform\\ へ展開し直す
(常にexeに同梱された最新版へ揃える)。

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
_BUNDLE_ITEMS = ("B_MARK.BAT", "A_SAVE.BAT", "mark_point", "dump_layers")

# 👑 GCOM_100は外部変形番号100〜109に対応する10ファイル分をまとめて1行に
# 書く形式(JWW_SMPL.BAT/Sample.jwf参照)。"=" の後をカンマ区切りで見た時、
# 何番目がどのCtrl+<文字>に対応するかはA=1,B=2,...J=10の並び。JwNavigator
# はCtrl+Jを使う(utils/layer_snapshot.pyのSAVE_KEY_VK)ため10番目、
# その次(11番目)がフォルダ名。実機のJw_win.jwf/kamo.JWFで実測確認済み
# (2026-09-11): "GCOM_100 =,,,,,,,,,B_MARK,C:\jww\JWW_EXT"。
_GCOM100_KEY = "GCOM_100"
_GCOM100_NAME_FIELD_INDEX = 9   # 0-indexed、Ctrl+Jは10番目
_GCOM100_DIR_FIELD_INDEX = 10
_GCOM100_MIN_FIELDS = 11
_EXTERNAL_TRANSFORM_FILENAME = "B_MARK"
_SKIP_PROFILE_NAMES = {"sample.jwf"}  # jw_cad同梱のひな形、実プロファイルではない


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


def ensure_gcom100_registered(jw_cad_exe_dir, log=None):
    """jw_cadのプロファイル(*.jwf/*.JWF)全部のGCOM_100を確認し、必要なら
    Ctrl+Jスロットへ外部変形の登録(ファイル名B_MARK、フォルダは今の
    external_transform_dir())を行う。既に別用途で使われているスロットは
    一切書き換えない。

    👑 ensure_deployed()と同じ理由で凍結exe(sys.frozen)の時だけ動作する。
    開発環境(python main.py)ではexternal_transform_dir()がbat/exeを
    実際には展開しない場所を指すため、ここで登録するとむしろ壊れた
    パスを書いてしまう(2026-09-11、実装中に気づいて追加した安全策)。
    """
    if not getattr(sys, "frozen", False):
        return
    if not jw_cad_exe_dir or not os.path.isdir(jw_cad_exe_dir):
        return

    target_dir = external_transform_dir()

    seen = set()
    jwf_paths = []
    for pattern in ("*.jwf", "*.JWF"):
        for p in glob.glob(os.path.join(jw_cad_exe_dir, pattern)):
            key = os.path.normcase(os.path.abspath(p))
            if key not in seen:
                seen.add(key)
                jwf_paths.append(p)

    for jwf_path in jwf_paths:
        if os.path.basename(jwf_path).lower() in _SKIP_PROFILE_NAMES:
            continue
        _ensure_gcom100_in_file(jwf_path, target_dir, log=log)


def _ensure_gcom100_in_file(jwf_path, target_dir, log=None):
    # 👑 実機のjwfに、過去の手編集由来と見られるcp932非適合バイト列が
    # GCOM_100行とは無関係な箇所に混ざっているのを実測で確認した
    # (2026-09-11)。ファイル全体をテキストとしてdecode→encodeし直すと、
    # その箇所が書き込み時にエラーになる(直そうとしている訳でもないのに
    # 巻き添えで壊れる)。そのため、GCOM_100の行だけをバイト列のまま
    # 特定して置き換え、それ以外は元のバイトに一切触れない方式にする。
    name = os.path.basename(jwf_path)
    try:
        raw = open(jwf_path, "rb").read()
    except Exception as e:
        if log:
            log(f"⚠️ {name}の読み込みに失敗したためGCOM_100確認をスキップしました: {e}")
        return

    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    key_bytes = _GCOM100_KEY.encode("ascii")
    lines = raw.split(newline)

    changed = False
    for i, line_bytes in enumerate(lines):
        if not line_bytes.startswith(key_bytes):
            continue
        if b"=" not in line_bytes:
            break
        try:
            line_text = line_bytes.decode("cp932")
        except UnicodeDecodeError:
            if log:
                log(f"⚠️ {name}のGCOM_100行の文字コードが想定と違うため、自動登録をスキップしました。")
            break
        prefix, _, rest = line_text.partition("=")
        fields = rest.split(",")
        while len(fields) < _GCOM100_MIN_FIELDS:
            fields.append("")
        current_name = fields[_GCOM100_NAME_FIELD_INDEX].strip()
        current_dir = fields[_GCOM100_DIR_FIELD_INDEX].strip()

        new_dir = None
        if current_name == "":
            fields[_GCOM100_NAME_FIELD_INDEX] = _EXTERNAL_TRANSFORM_FILENAME
            new_dir = target_dir
            if log:
                log(f"🔧 {name}のGCOM_100(Ctrl+J)にB_MARKを新規登録しました: {target_dir}")
        elif current_name == _EXTERNAL_TRANSFORM_FILENAME:
            if current_dir != target_dir:
                new_dir = target_dir
                if log:
                    log(f"🔧 {name}のGCOM_100登録先を更新しました: {current_dir} → {target_dir}")
        else:
            if log:
                log(
                    f"⚠️ {name}のGCOM_100(Ctrl+J)は別の外部変形({current_name})が"
                    "既に使用中のため、自動登録をスキップしました。"
                    "レイヤ保存機能を使うにはconfig/keybind_setup.mdを参照して手動で調整してください。"
                )

        if new_dir is not None:
            fields[_GCOM100_DIR_FIELD_INDEX] = new_dir
            new_line_text = prefix + "=" + ",".join(fields)
            lines[i] = new_line_text.encode("cp932")
            changed = True
        break  # GCOM_100行は1ファイルに1つのはず

    if not changed:
        return

    try:
        backup_path = jwf_path + ".bak_jwnavigator"
        if not os.path.exists(backup_path):
            shutil.copy2(jwf_path, backup_path)
        new_raw = newline.join(lines)
        with open(jwf_path, "wb") as f:
            f.write(new_raw)
    except Exception as e:
        if log:
            log(f"⚠️ {name}への書き込みに失敗しました: {e}")
# ===== ✂️ utils/external_transform_setup.py END ✂️ =====
