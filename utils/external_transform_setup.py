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
_GCOM100_NAME_FIELD_INDEX = 9   # 0-indexed、Ctrl+Jは10番目
_GCOM100_DIR_FIELD_INDEX = 10
_GCOM100_MIN_FIELDS = 11
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
_GCOM110_NAME_FIELD_INDEX = 0   # 0-indexed、Ctrl+KはGCOM_110の1番目
_GCOM110_DIR_FIELD_INDEX = 10
_GCOM110_MIN_FIELDS = 11
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


def ensure_gcom100_registered(jw_cad_exe_dir, log=None):
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
    for jwf_path in jwf_paths:
        if os.path.basename(jwf_path).lower() in _SKIP_PROFILE_NAMES:
            continue
        for key, name_idx, dir_idx, min_f, filename, label in (
            (_GCOM100_KEY, _GCOM100_NAME_FIELD_INDEX, _GCOM100_DIR_FIELD_INDEX,
             _GCOM100_MIN_FIELDS, _EXTERNAL_TRANSFORM_FILENAME, "Ctrl+J"),
            (_GCOM110_KEY, _GCOM110_NAME_FIELD_INDEX, _GCOM110_DIR_FIELD_INDEX,
             _GCOM110_MIN_FIELDS, _FAST_SAVE_FILENAME, "Ctrl+K"),
        ):
            result = _ensure_gcom_slot_in_file(
                jwf_path, target_dir, key, name_idx, dir_idx, min_f, filename,
                label, log=log,
            )
            if result == "new":
                did_new_registration = True
            elif isinstance(result, tuple) and result[0] == "conflict":
                conflicts.append((os.path.basename(jwf_path), label, result[1]))

    return {
        "new_registration": did_new_registration,
        "conflicts": conflicts,
        "has_jw_win": has_jw_win_jwf(jw_cad_exe_dir),
    }


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


def _ensure_gcom_slot_in_file(
    jwf_path, target_dir, gcom_key, name_field_index, dir_field_index,
    min_fields, filename, key_label, log=None,
):
    # 👑 実機のjwfに、過去の手編集由来と見られるcp932非適合バイト列が
    # GCOM_1XX行とは無関係な箇所に混ざっているのを実測で確認した
    # (2026-09-11)。ファイル全体をテキストとしてdecode→encodeし直すと、
    # その箇所が書き込み時にエラーになる(直そうとしている訳でもないのに
    # 巻き添えで壊れる)。そのため、対象の行だけをバイト列のまま特定して
    # 置き換え、それ以外は元のバイトに一切触れない方式にする。
    name = os.path.basename(jwf_path)
    try:
        raw = open(jwf_path, "rb").read()
    except Exception as e:
        if log:
            log(f"⚠️ {name}の読み込みに失敗したため{gcom_key}確認をスキップしました: {e}")
        return False

    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    key_bytes = gcom_key.encode("ascii")
    lines = raw.split(newline)

    changed = False
    is_new_registration = False
    found_line = False
    conflict_with = None
    for i, line_bytes in enumerate(lines):
        if not line_bytes.startswith(key_bytes):
            continue
        found_line = True
        if b"=" not in line_bytes:
            break
        try:
            line_text = line_bytes.decode("cp932")
        except UnicodeDecodeError:
            if log:
                log(f"⚠️ {name}の{gcom_key}行の文字コードが想定と違うため、自動登録をスキップしました。")
            break
        prefix, _, rest = line_text.partition("=")
        fields = rest.split(",")
        while len(fields) < min_fields:
            fields.append("")
        current_name = fields[name_field_index].strip()
        current_dir = fields[dir_field_index].strip()

        new_dir = None
        if current_name == "":
            fields[name_field_index] = filename
            new_dir = target_dir
            is_new_registration = True
            if log:
                log(f"🔧 {name}の{gcom_key}({key_label})に{filename}を新規登録しました: {target_dir}")
        elif current_name == filename:
            if current_dir != target_dir:
                new_dir = target_dir
                if log:
                    log(f"🔧 {name}の{gcom_key}登録先を更新しました: {current_dir} → {target_dir}")
            elif log:
                # 👑 2026-09-16: 「既に正しく登録済みなので何もしなかった」
                # 場合も痕跡を残す。kosakaPCの調査で、ログに何も出ない状態が
                # 「確認した上で正常」なのか「そのファイルを見ていない」のか
                # 区別できず原因切り分けに丸1日かかったため。
                log(f"✅ {name}の{gcom_key}({key_label})は既に登録済みです: {current_dir}")
        else:
            conflict_with = current_name
            if log:
                log(
                    f"⚠️ {name}の{gcom_key}({key_label})は別の外部変形({current_name})が"
                    "既に使用中のため、自動登録をスキップしました。"
                    "レイヤ保存機能を使うにはconfig/keybind_setup.mdを参照して手動で調整してください。"
                )

        if new_dir is not None:
            fields[dir_field_index] = new_dir
            new_line_text = prefix + "=" + ",".join(fields)
            lines[i] = new_line_text.encode("cp932")
            changed = True
        break  # 対象のGCOM_1XX行は1ファイルに1つのはず

    if not found_line and log:
        # 👑 2026-09-16: 行自体が無いプロファイルは今まで無言で素通りして
        # いた。jw_cadが実際に読むのは Jw_win.jwf なので、そこに行が無いと
        # 「登録したはずなのにCtrl+J/Ctrl+Kが効かない」状態になり、しかも
        # ログに何の痕跡も残らない(kosakaPCの調査で判明)。
        log(
            f"⚠️ {name}に{gcom_key}の行がありません。"
            f"このプロファイルには{key_label}の外部変形を登録できませんでした。"
        )

    if conflict_with:
        return ("conflict", conflict_with)

    if not changed:
        return None

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
        return None

    return "new" if is_new_registration else "updated"
# ===== ✂️ utils/external_transform_setup.py END ✂️ =====
