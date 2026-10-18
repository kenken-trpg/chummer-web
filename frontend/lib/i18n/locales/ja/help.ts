/** ツールチップのヘルプ — 計算値の式と内訳。日本語。 */
export const JA_HELP = {
  "help.open": "{label} の説明",
  "help.base": "基本値",
  "help.bonus": "修正（資質・ウェア・装備など）",
  "help.bonusOther": "その他（重複しない分など）",
  "help.total": "合計",
  "help.limit.physical": "身体リミット = (STR×2 + BOD + REA) ÷ 3（切り上げ）",
  "help.limit.mental": "精神リミット = (LOG×2 + INT + WIL) ÷ 3（切り上げ）",
  "help.limit.social": "社交リミット = (CHA×2 + WIL + ESS※) ÷ 3（切り上げ）※ESSは先に切り上げ",
  "help.limit.note": "技能テストでヒットとして数えられる上限（SR5 p.47）",
  "help.cm.physical": "身体ダメージトラック = 8 + BOD ÷ 2（切り上げ）",
  "help.cm.stun": "精神ダメージトラック = 8 + WIL ÷ 2（切り上げ）",
  "help.cm.note": "埋まったマス 3 つごとにテストへ −1（SR5 p.169）",
  "help.cm.vehicle":
    "身体ダメージトラック = Home Node {name} のもの（ヴィークル 12・ドローン 6・人型ドローン（Drones: Anthro）8 ＋ 強靱力 ÷ 2 ＋ 改造）",
  "help.cm.homeNode":
    "マトリックス・コンディション・モニター = Home Node {name} の 8 + 機器レーティング ÷ 2（切り上げ）",
  "help.cm.core": "Core Damage Track = 8 + DEP ÷ 2（切り上げ）。A.I. に精神ダメージトラックは無い",
  "help.init.value": "イニシアティブ = REA + INT",
  "help.init.dice": "イニシアティブ・ダイス = 1D6 + 追加ダイス（最大 5D6）",
  "help.init.note": "各イニシアティブ・パス終了時に −10（SR5 p.159）",
  "help.attr.BOD": "強靱力。ダメージ抵抗、身体ダメージトラック、身体リミットに効く",
  "help.attr.AGI": "敏捷力。射撃・近接など体を使う技能の多くに効く",
  "help.attr.REA": "反応力。イニシアティブ、防御テスト、操縦に効く。身体リミットにも入る",
  "help.attr.STR":
    "筋力。近接ダメージ、投擲距離、持ち運べる重さに効く。身体リミットでは 2 倍して数える",
  "help.attr.WIL": "意志力。精神ダメージトラック、ドレイン抵抗、精神・社交リミットに効く",
  "help.attr.LOG": "論理力。電子・技術系技能やマトリックスに効く。精神リミットの主な源",
  "help.attr.INT": "直観力。イニシアティブ、知覚、防御テストに効く。精神リミットにも入る",
  "help.attr.CHA": "魅力。交渉・威圧など対人技能に効く。社交リミットの主な源",
  "help.attr.EDG": "エッジ。1 セッションに使える回数。テストの振り直しや限界突破に使う",
  "help.attr.MAG": "魔力。呪文・召喚・アデプトパワーの強さ。エッセンスが減ると下がる",
  "help.attr.RES": "共振力。複合体やスプライトの強さ。エッセンスが減ると下がる",
  "help.attr.DEP": "Depth。A.I. の特殊能力値。EDG の上限になる",
  "help.avail.what": "入手値（Avail）：品物の手に入れにくさ。数字が大きいほど難しい",
  "help.avail.suffix": "末尾の R は所持に許可が要る（Restricted）、F は所持自体が違法（Forbidden）",
  "help.avail.chargen":
    "作成時は入手値がこの値を超える品物を買えない（標準 12）。キャリア中は入手テストで手に入れる",
  "help.deviceRating": "作成時に買える品物の機器レーティング上限（標準 6）",
  "help.gradeHint":
    "ウェアの等級。上の等級ほどエッセンスの消費が減り、価格と入手値が上がる。作成時に使えない等級は設定で決まる（標準では Betaware 以上は不可）",
  "help.skill.pool": "テストのダイス = 技能レーティング + 関連能力値（+ 修正）",
  "help.skill.spec": "専門化：その用途のテストに +2 ダイス。作成時はカルマ 1 点、キャリアは 7 点",
  "help.skill.expertise": "熟達（Expertise）：専門化を置き換えて +3 ダイス（キャリアのみ）",
  "help.skill.default":
    "未習得でも「デフォルティング」で振れる技能は、関連能力値 −1 でテストする（SR5 p.130）",
  "help.skill.cap": "作成時のレーティング上限。1 つだけ上限まで上げられる（資質 Aptitude で +1）",
  "help.group.members": "含まれる技能：{skills}",
  "help.group.sep": "、",
  "help.group.cost":
    "作成時は技能グループ・ポイント 1 点で 1 レーティング。カルマでは新しいレーティング × 5 点（SR5 p.107）",
  "help.group.break":
    "中の技能を 1 つだけ上げたり専門化を取ったりすると、グループとしては扱えなくなる。全部を同じレーティングに揃えると戻る",
  "help.matrix.attack":
    "アタック（ATK）：相手のデータやアイコンを壊す不正アクセス系の行動に使う。攻撃されると自分のテストにも使われる",
  "help.matrix.sleaze":
    "スリーズ（SLZ）：気づかれずに侵入・潜伏する行動に使う。相手のマトリックス知覚に対抗する",
  "help.matrix.dataprocessing":
    "データプロセシング（DP）：編集・検索・マークの維持など、静かな行動に使う。デッキのイニシアティブにも効く",
  "help.matrix.firewall":
    "ファイアウォール（FW）：相手の攻撃・侵入に対する防御。テストの対抗値になる",
  "help.matrix.array":
    "この 4 つの値はデッキごとに決まった組み合わせで、並べ替えて割り当てる。1 ターンに 1 回、無料行動で 2 つを入れ替えられる（SR5 p.222）",
  "help.knowledge.what":
    "知識技能：関連能力値は LOG か INT。区分は学術・専門・興味・ストリート・言語",
  "help.knowledge.free": "作成時の無料枠は (INT + LOG) × 2 点。母語が 1 つ無料になる",
  "help.knowledge.cost": "無料枠を使い切ったあとはカルマ 1 点で 1 レーティング。専門化も 1 点",
  "help.exotic.what":
    "Exotic 技能：対象（武器の種類など）ごとに別の技能として持つ。同じ技能を対象違いで複数持てる",
  "help.exotic.nodefault":
    "未習得ではデフォルティングで振れない。使うには必ずレーティングが要る（SR5 p.130）",
  "help.essence.what":
    "エッセンス：生身の度合い。誰でも 6 から始まり、サイバーウェアとバイオウェアで減る",
  "help.essence.magic": "減った分だけ魔力と共振力の上限も下がる（端数は切り上げで 1 段）",
  "help.essence.zero": "0 になると死亡。作成時は 0 より大きい値を残す必要がある",
  "help.essence.grade": "等級の倍率（C / B の表示）で、同じウェアでも消費が変わる",
  "help.quality.positive": "有利な資質はカルマで買う。作成時の上限は 25 カルマ分（設定で変わる）",
  "help.quality.negative": "不利な資質はカルマが戻るが、戻せるのも 25 カルマ分まで",
  "help.quality.career": "キャリア中の買い足し・買い取りはカルマ 2 倍が標準（SR5 p.72）",
  "help.vehicle.statsLabel": "ステータス",
  "help.vehicle.stats":
    "HND 操縦値／SPD 最高速度／ACC 加速値／BOD 強靱力／ARM 装甲値／PLT パイロット／SNR センサー",
  "help.vehicle.pilot": "PLT はオートパイロットの腕前。自律行動やリガー時のテストに使う",
  "help.vehicle.body": "BOD は頑丈さ。ダメージ抵抗と、改造に使えるスロットの量を決める",
  "help.vehicle.slots":
    "改造スロットは Rigger 5.0 の 6 系統（Powertrain・Protection・Weapons・Body・Electromagnetic・Cosmetic）ごとに別枠。各系統の上限 ＝ BOD ＋ その車種が持つ追加枠",
  "help.vehicle.slotsDrone":
    "ドローンは系統に分けず 1 つのプール（上限 ＝ BOD）。スロットを返す改造はその分だけ上限が増える",
  "help.weapon.statsLabel": "データ",
  "help.weapon.acc":
    "Acc（精度）：この武器で出せるヒットの上限。射撃・近接テストのリミットとして使う",
  "help.weapon.dv": "DV（ダメージ値）：命中したときのダメージ。末尾 P は身体、S は精神",
  "help.weapon.ap": "AP（装甲貫通）：相手の装甲をこの分だけ下げる。−2 なら抵抗側の装甲が 2 減る",
  "help.weapon.rc": "RC（反動補正）：連射で溜まる反動をこの分だけ打ち消す",
  "help.weapon.mode": "発射モード：SS 単発／SA 半自動／BF 3 点バースト／FA フルオート",
  "help.weapon.ammo":
    "装弾数と装填方式（(c) クリップ／(m) 弾倉／(b) 折り式／(d) ドラム／(ml) 手詰め）",
  "help.weapon.reach": "Reach（間合い）：近接戦で相手より長いと、その差がテストのボーナスになる",
  "help.armor.statsLabel": "装甲値",
  "help.armor.value": "装甲値：ダメージ抵抗のダイスに足す値（SR5 p.169）",
  "help.armor.stack":
    "着ている装甲のうち装甲値が最大の 1 着だけが効く。他の着分は改造の上乗せだけを持ち込む",
  "help.armor.capacity": "キャパシティ：この装甲に入れられる改造の量。使用量／上限で表示する",
  "help.armor.equipped": "装備していない装甲は装甲値に数えない",
  "help.contact.statsLabel": "コンタクトの値",
  "help.contact.connection":
    "コネ値：相手の人脈と力。高いほど良い品・良い情報に手が届く（SR5 p.388）",
  "help.contact.loyalty": "忠実値：相手がどれだけ親身か。高いほど無理を聞き、裏切りにくい",
  "help.contact.cost": "作成時のカルマはコネ値＋忠実値で、コンタクト値から払う",
  "help.spell.statsLabel": "呪文データ",
  "help.spell.drain":
    "ドレイン：術者が受ける反動。F は唱えるときに選ぶフォースで、F−3 ならフォース −3（最低 2）",
  "help.spell.drainResist": "ドレイン抵抗は意志力＋様式の能力値で振り、抵抗しきれない分を食らう",
  "help.spell.force": "フォースが魔力以下なら精神ダメージ、超えると身体ダメージになる（SR5 p.281）",
  "help.spell.range": "射程（LOS 視線／T 接触／範囲）と持続（瞬間／維持／永続）",
  "help.ware.statsLabel": "ウェアの値",
  "help.ware.essence": "ESS −n はこの品が食うエッセンス。等級の倍率がかかった後の値",
  "help.ware.capacity":
    "キャパシティ：この品の中に入れられる量（使用／上限）。サイバー手足や筐体が持つ",
  "help.bio.statsLabel": "このタブの合計",
  "help.bio.what":
    "バイオウェア：培養した生体組織を体に植える。サイバーウェアと同じようにエッセンスを消費する（SR5 p.459）",
  "help.bio.essence": "Essence は残っている合計で、括弧内はバイオウェアで減った分だけ",
  "help.bio.spent": "消費¥はこのタブ分ではなく、装備や資質も含めた支出の合計",
  "help.cf.statsLabel": "複合体の値",
  "help.cf.fv": "フェイディング：L は唱えるときに選ぶレベルで、L−1 ならレベル −1（最低 2）",
  "help.cpower.what":
    "Infected の資質・Dracoform の資質が開くタブ。資質が決めた分類（Infected・Drake）のパワーを、それぞれのカルマで買う",
  "help.cpower.offer":
    "一覧に出るのは、前提条件（Infected の種類やほかのパワー）を満たしたものだけ",
  "help.cpower.granted": "資質が最初から持たせるパワーはここに出ない。資質タブの資質の欄に並ぶ",
  "help.aiprog.price":
    "1 つにつき 5 カルマ、Advanced Programs は 8 カルマ（DT）。作成後に足しても同じ価格",
  "help.aiprog.inherent": "資質 Inherent Program で選んだ 1 つは無料で、資質を外すと消える",
  "help.cf.fade": "フェイディング抵抗は意志力＋共振力で振り、抵抗しきれない分を食らう",
  "help.cf.level": "レベルが共振力以下なら精神ダメージ、超えると身体ダメージになる",
  "help.cf.target": "対象（ペルソナ／機器／ファイル／スプライトなど）と持続",
  "help.spirit.statsLabel": "精霊の値",
  "help.spirit.force": "F（フォース）：精霊の強さ。能力値もテストのダイスもここから決まる",
  "help.spirit.services": "助力：命じられる残り回数。1 つの仕事で助力を 1 回使う",
  "help.spirit.bound": "束縛すると呼び直せるが原質が要る。ただの召喚は夜明けで消える",
  "help.sprite.statsLabel": "スプライトの値",
  "help.sprite.level": "L（レベル）：スプライトの強さ。マトリックス値とテストのダイスの基準",
  "help.sprite.tasks": "タスク：命じられる残り回数。1 つの仕事で 1 タスク使う",
  "help.sprite.registered": "登録すると残り続ける。コンパイルしただけなら再起動で消える",
  "help.initiation.statsLabel": "等級とカルマ",
  "help.initiation.karma": "1 等級あたり 10 ＋ 等級×3 カルマ（等級 1 は 13、2 は 16…）",
  "help.initiation.discount":
    "グループ・オーディール・師事のそれぞれで 10% 引き（重ねられる、SR5 p.325）",
  "help.initiation.metamagic": "1 等級につきメタマジックか流儀を 1 つ選べる",
  "help.life.statsLabel": "生活費",
  "help.life.monthly": "月額 ＝ 基本額 ×（1＋修正％）＋ ライフスタイル資質の分",
  "help.life.months": "その月額に、払う期間（月数など）を掛けたものが総額",
  "help.life.lp": "LP：自分で組むライフスタイルで資質に使える点数（使用／上限）",
  "help.matrix.statsLabel": "マトリックス値",
  "help.matrix.deviceRating":
    "DR（機器レーティング）：機器の素の性能。持ち主が操作していないときのテストに使う",
  "help.matrixmod.statsLabel": "電子改造の値",
  "help.matrixmod.what":
    "電子改造（DT p.66）：改造自体の追加費用はないが、部品・工具は別途必要。材料を配分し、成功した施工を登録すると効果が有効になる",
  "help.matrixmod.array":
    "デッキでは配列の枠どうしで点を移すものがある（片方 +1、もう片方 −1）。合計は増えない",
  "help.matrixmod.included":
    "「標準装備」と出ているものは機器に最初から付いており、価格もかからない",
  "help.prio.statsLabel": "表の読み方",
  "help.prio.attrCell": "能力値の欄の「6 (2)」は、通常の能力値点 6 と特殊能力値点 2",
  "help.prio.special": "特殊能力値点はエッジ・魔力・共振力に使う。通常の点とは混ぜられない",
  "help.prio.skillCell": "技能の欄の「24/2」は、技能点 24 と技能グループ点 2",
  "help.prio.magicCell": "魔法／共振の欄はタレントと、ついてくる呪文・複合体の無料枠",
  "help.adept.statsLabel": "パワーポイント",
  "help.adept.pp": "アデプトのパワーポイントは魔力と同数。パワーを取った分だけ減る",
  "help.adept.mystic":
    "ミスティックアデプトは 1 点 5 カルマで買う。買わなかった分の魔力は呪文用に残る",
  "help.adept.way": "Way（流儀）の資質は対象のパワーを安くする。割引の総量は魔力 ÷ 4（切り上げ）",
  "help.martial.statsLabel": "格闘技スタイルと技法",
  "help.martial.style": "格闘技スタイルは 7 カルマ（品目ごとに別のカルマのことがある）",
  "help.martial.technique": "技法は 1 つ 5 カルマ。資質で付いてくる分は無料",
  "help.martial.chargen": "作成時は格闘技スタイル 1 つ・技法 5 つまで。キャリア中は上限なし",
  "help.gear.statsLabel": "装備の値",
  "help.gear.rating":
    "R（レーティング）：性能の段階。上げると価格も入手値も上がることが多い。上限は品目ごと",
  "help.gear.capacity": "容量 n/m：この装備に部品を積める量（m）と、いま使っている量（n）",
  "help.gear.qty": "×n は個数。価格は個数倍になる",
  "help.points.attr": "能力値点 n/m：使った点／このキャラクターが持つ点。余っても他には回せない",
  "help.points.special": "特殊点 n/m：エッジ・魔力・共振力にだけ使える点。通常の能力値点とは別勘定",
  "help.points.skills": "技能点 n/m：1 点で技能レーティング 1。技能グループ点とは別枠",
  "help.points.knowledge": "知識点 n/m：無料枠は (INT + LOG) × 2 点。母語が 1 つ無料になる",
  "help.points.contacts":
    "コンタクト n/m (+k)：無料枠 m は CHA × 3（設定で変わる）。+k は超えて買った分で、コネ値 ＋ 忠実値がそのままカルマになる",
  "help.points.martial": "格闘技スタイル n/m ・ 技法 n/m：作成時の上限。超える分はカルマで買う",
  "help.points.advancement": "成長カルマ：キャリアに入ってから能力値・技能を上げるのに使ったカルマ",
  "help.points.negativeKarma": "不利な資質で戻るカルマの上限。設定で変わる",
  "help.points.spells":
    "呪文 n/m (+k)：タレントの無料枠 m と、カルマで買い足した分 k（標準 1 つ 5 カルマ）",
  "help.points.complexForms":
    "複合体 n/m (+k)：タレントの無料枠と、カルマで買い足した分（標準 1 つ 4 カルマ）",
  "help.livingPersona":
    "生体ペルソナ：テクノマンサー自身がデッキの代わりになる。DR ＝ 共振力、ATK ＝ CHA、SLZ ＝ INT、DP ＝ LOG、FW ＝ WIL",
  "help.attr.wareBonus": "「ウェア+n」はサイバー／バイオウェアによる加算。素の値の上限とは別に乗る",
  "help.attr.limbAverage":
    "「リム平均」が出ているときの STR / AGI は、全肢の平均（義肢はその肢の値、生身は素の値）",
  "help.attr.unimplemented":
    "未実装ボーナス：カタログにあるがこの計算機がまだ扱えない修正。値には入っていない",
  "help.flag.ambidextrous": "両利き：利き手でない側で撃つ・殴るときの不利を受けない",
  "help.flag.erased": "Erased：マトリックス上に残った自分の記録が、放っておくと消えていく",
  "help.flag.excon": "Ex-Con：前科者。社会的な扱いが悪くなる代わりにカルマが戻る",
  "help.flag.overclock":
    "Overclocker：いちばん性能の高いデッキのマトリックス値 1 つ（ふつうアタック）に +1",
  "help.flag.specialMod":
    "特別改造 n/m：資質で増える枠で、これを要求する武器アクセサリの数を数えている",
  "help.flag.fihp": "Friends in High Places：伝手が要る場面で便宜を受けられる",
  "help.flag.madeMan": "Made Man：組織の一員。後ろ盾が付くかわりに抜けられない",
  "help.flag.trustfund":
    "Trust Fund：等級に応じたライフスタイルの月額が無料になる（1 中流／2 低所得／3 高級／4 中流）",
  "help.flag.dealer": "Dealer Connection：この分類のヴィークルが 10% 引きで買える",
  "help.career.rewards":
    "ここで足したカルマと新円は、作成時の予算ではなくキャリア中の収入として積む",
  "help.career.log": "1 行ずつ残るので、どのランで何をもらったか後から辿れる",
  "help.career.edit":
    "式から出る分とは別に、GM が与えた分を手で上乗せする欄。式の値そのものは動かない",
  "help.granted.what":
    "資質・ウェア・アデプトパワー・導師精霊が与える技能。ここで選んでも技能点は減らない",
  "help.granted.where": "与えている側のタブにある同じ選択を写したもの。どちらで選んでも同じ",
  "help.talent.what": "プライオリティのタレントが配る技能。選ぶだけで、技能点は使わない",
  "help.talent.rating": "決まったレーティングまで無料で上がる。その上に技能点で買い足せる",
  "help.talent.change": "選び直すと前の技能から無料分だけ下がる。買い足した分はそのまま残る",
  "help.heldGear.statsLabel": "中に入れる装備",
  "help.heldGear.what":
    "ケミカルグランドや自動注射器のように、ウェアが中に抱える装備。入れたものの価格はウェアとは別に掛かる",
  "help.drug.statsLabel": "ドラッグの値",
  "help.drug.effect": "効果は「使用中」の間だけ能力値などに乗る。外せば元に戻る",
  "help.drug.onset": "発現（Onset）：摂ってから効き始めるまでの時間。0 は即時",
  "help.drug.vector":
    "摂取方法（注射・吸入・経口・接触）。同じドラッグでも方法で発現の速さが変わる",
  "help.drug.testLabel": "依存症テスト",
  "help.drug.pool":
    "依存症テストのプール ＝ BOD ＋ WIL（肉体的）／LOG ＋ WIL（精神的）（SR5 p.414）",
  "help.drug.threshold": "依存症閾値がそのテストの目標ヒット数。届かないと依存症が 1 段進む",
  "help.drug.addicted":
    "括弧内はすでに依存症になっている場合のプール。初回だけ変える資質がある（Drug Tolerant は初回 +2、CF p.54）",
  "help.drug.rating": "依存症レーティング：抜けようとするときに相手になる値。大きいほど抜けにくい",
  "help.drug.speed": "発現までの秒数。0 は即時",
  "help.drug.duration": "効果が続く時間。切れたあとにクラッシュが来るものがある",
  "help.drug.crash": "クラッシュ：効果が切れたときに受ける反動のダメージ",
  "help.drug.grade": "等級の倍率は価格に掛かる。上の等級ほど入手値も上がる",
  "help.drug.parts":
    "基剤（Foundation）1 つの上にブロックと強化剤を重ねる。何を重ねられるかは基剤が決める（CF p.190）",
  "help.sensor.statsLabel": "センサーの値",
  "help.sensor.nest": "筐体 → センサー → 機能の 3 段。機能は筐体の容量に収まる範囲で積む",
  "help.sensor.capacity": "容量 n/m：この筐体に積める量（m）と、いま使っている量（n）",
  "help.sensor.rating": "R（レーティング）：センサーの精度。知覚テストのリミットになる",
  "help.optics.statsLabel": "視覚・聴覚機器の値",
  "help.optics.nest": "強化はこの機器に積む。サイバーウェアの目・耳とは別の枠で、容量は共有しない",
  "help.optics.capacity": "容量 n/m：この機器に積める強化の量（m）と、いま使っている量（n）",
  "help.optics.rating": "R（レーティング）：強化の段階。同じ強化を重ねても効果は足し合わない",
  "help.program.statsLabel": "プログラムの値",
  "help.program.deckSlot":
    "搭載本数に制限はない。作動中のプログラムだけが同時実行枠を使う。購入・搭載時は停止状態で、チェックで作動を切り替える",
  "help.program.slot":
    "1 本ごとに搭載先のプログラムスロットを 1 つ使う。デッキや RCC 側に n/m で出る",
  "help.program.rating": "R（レーティング）があるものは段階で効果が変わる。上限は品目ごと",
  "help.program.loose": "どこにも積んでいないプログラムはここに溜まる。買ってあるだけでは働かない",
  "help.vehmod.statsLabel": "改造の値",
  "help.vehmod.slots": "スロット n：この改造が車体から食う枠。系統ごとの上限と突き合わせる",
  "help.vehmod.rating":
    "R（レーティング）：改造の段階。価格やスロットがレーティングで変わるものがある",
  "help.vehmod.capacity": "容量 n/m：この改造自身が抱えられる量（センサーやウェアを積むもの）",
  "help.vehmod.included":
    "「標準装備」と出ているものは車種に最初から付いており、スロットを使わず価格もかからない",
  "help.vehmount.statsLabel": "マウントの値",
  "help.vehmount.slots": "スロット n：マウント自身が車体から食う枠。載せる武器は枠を食わない",
  "help.vehmount.weapon":
    "載せられるのは武器タブで買ってある武器だけ。ここでは選ぶだけで、買うことはできない",
  "help.vehmount.included": "「標準装備」のマウントは車種に最初から付いており、外せない",
  "help.vehgear.statsLabel": "車内の装備の値",
  "help.vehgear.what": "車体に固定する改造ではなく、車内に積んでいるだけの装備。スロットは食わない",
  "help.vehgear.rating": "R（レーティング）：装備の段階。価格はレーティングで変わる",
  "help.meta.statsLabel": "メタタイプの選び方",
  "help.meta.special": "特殊点はエッジ・魔力・共振力にだけ使える。通常の能力値点とは別勘定",
  "help.meta.karma":
    "カルマ作成では、メタタイプそのものにカルマを払う（オーク 50、トロール 100 など）",
  "help.meta.variant": "メタバリアントは同じメタタイプの亜種。能力値の上下限と資質が変わる",
  "help.meta.talent": "タレントは魔法・共振の素質。メタタイプを変えても選び直しは要らない",
  "help.foci.statsLabel": "収束具の上限",
  "help.foci.count": "同時に結合できる数は魔力まで（氣収束具もこの数に入る）",
  "help.foci.force": "結合した収束具のフォース合計は魔力×2 まで（超えるとどれも使えない）",
  "help.foci.bind": "結合カルマはフォースと同数。買っただけ・作っただけでは働かない",
  "help.foci.craft":
    "クラフトは術式＋原質フォース×20¥。定価で買うより安いが、テストに失敗すると無駄になる",
  "help.sub.statsLabel": "等級とカルマ",
  "help.sub.karma": "1 等級あたり 10 ＋ 等級×3 カルマ（等級 1 は 13、2 は 16…）",
  "help.sub.discount": "ネットワーク・タスク・師事のそれぞれで 10% 引き（重ねられる）",
  "help.sub.echo": "1 等級につきエコーを 1 つ選べる。共振力の上限も等級のぶんだけ伸びる",
} as const;
