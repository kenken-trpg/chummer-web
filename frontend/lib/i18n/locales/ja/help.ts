/** ツールチップのヘルプ — 計算値の式と内訳。日本語。 */
export const JA_HELP = {
  "help.open": "{label} の説明",
  "help.base": "基本値",
  "help.bonus": "修正（資質・ウェア・装備など）",
  "help.bonusOther": "その他（重複しない分など）",
  "help.total": "合計",
  "help.limit.physical": "物理リミット = (BOD×2 + AGI + REA + STR) ÷ 3（切り上げ）",
  "help.limit.mental": "精神リミット = (LOG×2 + INT + WIL) ÷ 3（切り上げ）",
  "help.limit.social": "社会リミット = (CHA×2 + WIL + ESS) ÷ 3（切り上げ）",
  "help.limit.note": "技能判定でヒットとして数えられる上限（SR5 p.47）",
  "help.cm.physical": "物理モニター = 8 + BOD ÷ 2（切り上げ）",
  "help.cm.stun": "朦朧モニター = 8 + WIL ÷ 2（切り上げ）",
  "help.cm.note": "埋まったマス 3 つごとに判定へ −1（SR5 p.169）",
  "help.init.value": "イニシアチブ = REA + INT",
  "help.init.dice": "イニシアチブ・ダイス = 1D6 + 追加ダイス（最大 5D6）",
  "help.init.note": "戦闘ターンの行動順。1 行動ごとに −10（SR5 p.159）",
  "help.attr.BOD": "強靱力。ダメージ抵抗、物理モニター、物理リミットに効く",
  "help.attr.AGI": "敏捷力。射撃・近接など体を使う技能の多くに効く。物理リミットにも入る",
  "help.attr.REA": "反応力。イニシアチブ、防御判定、操縦に効く。物理リミットにも入る",
  "help.attr.STR": "筋力。近接ダメージ、投擲距離、持ち運べる重さに効く。物理リミットにも入る",
  "help.attr.WIL": "意志力。朦朧モニター、ドレイン抵抗、精神・社会リミットに効く",
  "help.attr.LOG": "論理力。電子・技術系技能やマトリックスに効く。精神リミットの主な源",
  "help.attr.INT": "直観力。イニシアチブ、知覚、防御判定に効く。精神リミットにも入る",
  "help.attr.CHA": "魅力。交渉・威圧など社会技能に効く。社会リミットの主な源",
  "help.attr.EDG": "エッジ。1 セッションに使える回数。判定の振り直しや限界突破に使う",
  "help.attr.MAG": "魔力。呪文・召喚・アデプトパワーの強さ。エッセンスが減ると下がる",
  "help.attr.RES": "共振力。複合フォームやスプライトの強さ。エッセンスが減ると下がる",
  "help.avail.what": "入手可能度（Avail）：品物の手に入れにくさ。数字が大きいほど難しい",
  "help.avail.suffix": "末尾の R は所持に許可が要る（Restricted）、F は所持自体が違法（Forbidden）",
  "help.avail.chargen":
    "作成時は入手可能度がこの値を超える品物を買えない（標準 12）。キャリア中は入手判定で手に入れる",
  "help.deviceRating": "作成時に買える機器のデバイスレーティングの上限（標準 6）",
  "help.gradeHint":
    "ウェアの品質。上のグレードほどエッセンスの消費が減り、値段と入手可能度が上がる。作成時に使えないグレードは設定で決まる（標準では Betaware 以上は不可）",
  "help.skill.pool": "判定ダイス = 技能レーティング + 関連能力値（+ 修正）",
  "help.skill.spec": "専門化：その用途の判定に +2 ダイス。作成時はカルマ 1 点、キャリアは 7 点",
  "help.skill.expertise": "熟達（Expertise）：専門化を置き換えて +3 ダイス（キャリアのみ）",
  "help.skill.default":
    "未習得でも「デフォルト」で振れる技能は、関連能力値 −1 で判定する（SR5 p.130）",
  "help.skill.cap": "作成時のレーティング上限。1 つだけ上限まで上げられる（資質 Aptitude で +1）",
  "help.matrix.attack":
    "アタック（ATK）：相手のデータやアイコンを壊す不正アクセス系の行動に使う。攻撃されると自分の判定にも使われる",
  "help.matrix.sleaze":
    "スリーズ（SLZ）：気づかれずに侵入・潜伏する行動に使う。相手のマトリックス知覚に対抗する",
  "help.matrix.dataprocessing":
    "データプロセシング（DP）：編集・検索・マークの維持など、静かな行動に使う。デッキのイニシアチブにも効く",
  "help.matrix.firewall":
    "ファイアウォール（FW）：相手の攻撃・侵入に対する防御。判定の対抗値になる",
  "help.matrix.array":
    "この 4 つの値はデッキごとに決まった組み合わせで、並べ替えて割り当てる。1 ターンに 1 回、無料行動で 2 つを入れ替えられる（SR5 p.222）",
} as const;
