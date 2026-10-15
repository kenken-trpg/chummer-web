/** 作成の流れ: プライオリティ・能力値・技能・資質・設定 — 日本語。 */
export const JA_CHARGEN = {
  "engine.life.ratingCap":
    "経歴による「{name}」の付与値 {rating} が上限 {cap} を超えます。上限超過分の精算は未対応のため、この組み合わせは使用できません。",

  "engine.life.skillGrantInvalid": "経歴が付与する技能「{name}」の定義を解決できません。",
  "engine.life.skillExcessLost":
    "「{name}」の付与は上限を超えるため、{lost}レベルは付与されません（{stage}）。",
  "engine.life.transferPending":
    "「{name}」の超過分を移し替えてください（残り{remaining}レベル）。",
  "engine.life.transferOrphan":
    "移し替え指定 {transfer} に対応する超過分がありません。指定を削除または修正してください。",
  "engine.life.transferInvalidTarget": "移し替え指定 {transfer} の行き先が条件を満たしません。",
  "engine.life.transferSourceChanged":
    "「{name}」の付与条件が変わったため、移し替え先を指定し直してください。",
  "engine.life.transferOverallocated":
    "「{name}」の移し替え指定は{requested}レベルで、超過分{total}レベルを超えています。",
  "engine.life.transferDuplicate": "移し替え指定 {transfer} が重複しています。",
  "engine.life.transferCapacity":
    "「{name}」へは{capacity}レベルまで移せますが、{requested}レベルが指定されています。",
  "engine.life.transferUnallocatable":
    "「{name}」の超過分のうち{lost}レベルは、条件を満たす技能に空きがないため付与されません。",

  "engine.life.purchaseInvalid": "技能「{name}」の購入指定が不正です。",
  "engine.life.purchaseCap":
    "「{name}」の購入後の値 {requested} が上限 {cap} を超えます。購入指定を修正してください。",
  "engine.life.groupPurchaseUnequal":
    "「{group}」の構成技能の無償値が揃っていないため、グループでは購入できません。個別に購入してください。",

  "life.transfer.title": "「{name}」の超過分",
  "life.transfer.source":
    "付与前 {before} ＋付与 {grant}（採用 {kept}）。移し替え {total} レベル、残り {remaining}。",
  "life.transfer.provisional": "先行する経歴の未解決項目により、この超過量は変わる場合があります。",
  "life.transfer.invalid":
    "この配分には不正な指定があります。対象の指定を削除し、追加し直してください。",
  "life.transfer.lost": "移せる技能に空きがないため、{count}レベルは付与されません。",
  "life.transfer.unknown": "不明な技能",
  "life.transfer.remove": "配分を削除",
  "engine.life.policyInvalid": "Life Module creation skill caps must be integers from 1 to 1000.",
  "life.transfer.target": "移し替え先の技能",
  "life.transfer.specific": "技能の具体的な対象",
  "life.transfer.ranks": "移すレベル数",
  "life.transfer.add": "この配分を追加",
  "life.transfer.failed": "保存できませんでした。入力を確認して再試行してください。",
  "life.transfer.caps": "経歴付与の上限: 能動技能 {active}／知識技能 {knowledge}。",
  "life.transfer.orphan": "対応する経歴または超過分がない配分（{ranks}レベル）があります。",
  "life.transfer.loss": "「{name}」は上限により{count}レベルが付与されません。",
  "life.moveEarlier": "この段階で1つ前へ",
  "life.moveLater": "この段階で1つ後へ",
  "life.freeSkill": "経歴付与: {count}",
  "life.groupUnequal": "経歴付与が不揃いのためグループ購入できません。",
  "life.groupConvert": "個別の購入へ変換",

  "engine.life.snapshotRequired":
    "The Life Module creation skill snapshot is missing or inconsistent. Review creation before entering career mode.",
  "engine.life.careerFrozen":
    "キャリア開始時の経歴・配分・購入入力は変更できません。技能の成長欄を使用してください。",
  "engine.life.advancementInvalid":
    "技能成長の開始値・上限・条件または履歴が一致しません。最後の成長から取り消して修正してください。",
  "engine.life.creationIncomplete":
    "作成チェックのエラーと未配分の技能超過分を解消してからキャリアを開始してください。",
  "engine.life.skillGrowthLine": "技能成長 +{levels}レベル",
  "engine.life.legacyCareer":
    "This career uses legacy Life Module calculations. Review it in creation mode to migrate to the new rules.",

  "life.growth.title": "Career skill advancement",
  "life.growth.note":
    "Creation grants, transfers and purchases are frozen. Buy advancement from the current rating. The purchase controls below show creation inputs.",
  "life.growth.kind": "Advancement type",
  "life.growth.target": "Skill or group to advance",
  "life.growth.levels": "Levels to add",
  "life.growth.add": "Buy advancement",
  "life.growth.undo": "Undo last skill advancement",

  "life.kind.attributes": "能力値",
  "life.kind.skills": "技能",
  "life.kind.skill_groups": "技能グループ",
  "life.kind.knowledge_skills": "知識技能",
  "life.kind.knowledge_categories": "知識カテゴリー",
  "life.kind.specializations": "専門化",
  "life.kind.qualities": "資質",

  "life.experimental":
    "Experimental support. Modules with unsupported mechanics are unavailable. Chummer resaves import as career snapshots because their module choices are not retained.",
  "engine.life.chum5StateInvalid":
    "この .chum5 のライフモジュール情報と技能値が一致しないか、保存形式に対応していません。JSON バックアップから復元してください。",
  "engine.life.chum5Unsupported":
    "LifeModule方式のキャラクターですが、経歴モジュールが見つからず選択履歴もないため読み込めません。元の .chum5 またはJSONバックアップから復元してください。",
  "engine.life.chum5Snapshot":
    "Chummerで再保存したライフモジュールのキャラクターを、保存済みの技能・能力値を保つキャリアスナップショットとして読み込みました。経歴の選択肢と超過移し替えの履歴は復元できません。経歴は記録として保持し、新たな成長はこの保存時点を基準に計算します。",
  "engine.export.chum5LifeModuleSetup":
    "ライフモジュールはキャラクター・対応設定XML・手順書をZIPで出力します。Chummerを終了し、設定XMLをChummerのsettingsフォルダーへコピーしてから、全体設定でLife Modulesを有効にしてください。Chummerで再保存すると選択肢・超過分の移し替え履歴が消え、このアプリへ再取り込みできません。JSONバックアップを保管してください。",
  "engine.life.chum5ModuleUnknown":
    "この .chum5 の経歴「{name}」がこのアプリのデータにありません。経歴を 1 つ落とすと以降の選択が別の経歴にずれるため、読み込みを中止しました。",

  "life.method": "Life Module",
  "life.note":
    "Choose a history for each stage. Further education and real life can repeat. Attribute and skill inputs are purchased ratings; module grants are added to the computed results.",
  "life.total": "Module karma: {karma}",
  "life.nuyen": "Module bonus funds: ¥{amount}",
  "life.freeQuality": "Free quality points: Positive {positive} / Negative {negative}",
  "life.pick": "Choose a module",
  "life.candidates": "Module candidates",
  "life.browseHint":
    "Select a candidate to review its details. Your history changes only when you press Add.",
  "life.previewHint": "Select a candidate to review its description, cost, and requirements.",
  "life.unavailable": "Cannot add (see details)",
  "life.choiceCount": "Choices to complete after adding: {count}",
  "life.stageFull": "This stage already has a module. Remove it first if you want to change it.",
  "life.add": "Add this module",
  "life.description": "Module description",
  "life.stageSelected": "Selected",
  "life.stagePending": "Not selected",
  "life.repeatable":
    "You can choose different modules for this stage. Each module, including its versions, can only be taken once.",
  "life.search": "Search modules (name, parent, description, source)",
  "life.noMatches": "No modules match your search. Try another search term.",
  "life.requires": "Requires: {requirements}",
  "life.requirementUnmet": "Requirements are not met",
  "life.remove": "Remove this module",
  "life.choice": "{name}: choose {kind}",
  "life.pending": "Choose an option",
  "life.unsupported": "Unavailable: contains unsupported effects",
  "life.empty": "No modules for this stage. Check the enabled rulebooks.",
  "engine.life.unknown": "Unknown Life Module: {name}",
  "engine.life.unsupported": "Life Module “{name}” has unsupported mechanics: {tags}",
  "engine.life.duplicateModule":
    "Life Module {name} can only be taken once, including its versions",
  "life.alreadyTaken": "This module or one of its versions is already taken",
  "engine.life.duplicateStage": "Duplicate life stage: {stage}",
  "engine.life.missingStage": "Choose a module for life stage: {stage}",
  "engine.life.choice": "Complete a choice in Life Module “{name}” ({slot})",
  "engine.life.specializationConflict":
    "The Life Module specialization for “{name}” conflicts with the existing selection",
  "engine.life.qualityUnknown": "Life Module quality “{name}” was not found",
  "engine.life.ratedQualityConflict":
    "Combining module-granted levels of “{name}” with a manual purchase of the same quality is not yet supported.",
  "engine.life.qualityChoiceConflict":
    "The extra selection for Life Module quality “{name}” conflicts with an existing selection. Different selections for the same quality are not yet supported together.",
  "engine.life.qualityLevelUnknown":
    "Quality “{name}” for a Life Module quality level was not found",
  "engine.life.requirement": "The requirements for Life Module “{name}” are not met",

  "meta.booksHidden":
    "この条件の種族のうち {count} 件は、使用ルールブックの設定で候補に出ていません",
  "meta.innate": "{name}の生得能力（追加カルマなし）",
  "meta.innateFixed": "生得付与・削除不可",
  "meta.innateQualities": "生得資質",
  "meta.innateQualitiesHint": "資質タブにも並びます。カルマはかからず、削除もできません",
  "meta.critterPowers": "クリッター・パワー",
  "meta.critterPowersHint":
    "このメタタイプがクリッターとして持つパワーです。資質ではないので、資質タブには出ません",
  "meta.retained":
    "現在の種族「{name}」は、この条件の新規選択候補にありません。別の種族を選ぶまで保持されます",
  "skills.points": "技能 {skills} ・ グループ {groups} ・ 知識 {knowledge}",
  "skills.careerNote": " ・ キャリアはカルマで成長（上限 R{max}）",
  "skills.chargenNote": " ・ 専門化は1点",
  "skills.granted": "ついてくる技能",
  "skills.grantedNote":
    "資質・ウェア・アデプト能力・メンター精霊が連れてくる技能です。ここで選んでも、それぞれのタブで選んでも同じものです。",
  "skills.talentLabel": "タレントでもらえる技能",
  "skills.talent": "タレントでもらえる技能（{qty} つを R{rating} で）",
  "skills.talentGroup": "タレントでもらえる技能グループ（{qty} つを R{rating} で）",
  "skills.talentPick": "{n} つ目",
  "skills.groups": "技能グループ",
  "skills.softBit": "ソフトR{rating}",
  "skills.default": "デフォルト {pool}",
  "skills.defaultFree": "デフォルト {pool}（−1なし）",
  "skills.defaultBlocked": "デフォルト不可",
  "skills.defaultHint": "未習得。関連能力値 {attr} から −1 して振ります（SR5 p.130）",
  "skills.specBit": "専門+{bonus}",
  "skills.specDisabled": "専門化の効果なし",
  "skills.active": "能動技能",
  "skills.rowHint": "{category}／関連能力値 {attr}／作成上限 {max}",
  "skills.attrSwap": "関連能力値 {attr}（{source} で差し替え）",
  "skills.specAttrSwap": "{spec} 使用時は {attr}",
  "skills.groupHint": "{group}：グループ内の技能をまとめて上げます（作成上限 {max}）",
  "skills.ratingHint": "レーティング（作成上限 {max}）",
  "skills.exotic": "Exotic技能",
  "skills.exoticNote":
    "対象の指定が技能そのものです。同じ Exotic を別対象で複数持てます。専門化の追加点は不要です。",
  "skills.emptyExotic": "まだありません。下のボタンから追加します。",
  "skills.addNamed": "{name} を追加",
  "skills.knowledge": "知識技能",
  "skills.knowDefault":
    "未取得の知識技能もデフォルトで振れます: INT {int} ／ LOG {log}（−1・SR5 p.130）",
  "skills.knowDefaultBlocked": " ／ {categories} はデフォルト不可",
  "skills.knowledgeFree": "無料枠は (INT + LOG) × 2 ・ 母語は1つ無料。",
  "skills.knowledgeCareerRange": "キャリアのレーティングは1〜{max}",
  "skills.knowledgeChargenRange": "作成時のレーティングは1〜6",
  "skills.rangeSuffix": "です。",
  "skills.knowledgeCareerCost": "追加はカルマ",
  "skills.karmaHint":
    "この技能の上から何レベルをカルマで買ったか。その分は技能点（知識技能点）を使わず、上げた後の値×2（知識技能は×1）カルマかかります。",
  "skills.karmaSpent": "カルマで上げた技能：{karma} カルマ（知識技能 {knowledge} カルマ）",
  "skills.knowledgeChargenCost": "専門化は知識点1",
  "skills.specKarma": "カルマで",
  "skills.specKarmaHint": "この専門化を技能点（知識技能点）ではなくカルマで買います。",
  "skills.custom": " （カスタム）",
  "skills.free": "無料",
  "skills.native": "母語",
  "skills.emptyKnowledge": "まだありません。カタログから追加するか、カスタム名で作れます。",
  "skills.searchKnowledge": "知識技能を検索",
  "skills.customName": "カスタム知識名",

  // --- vehicles / drones --------------------------------------------------
  "skills.addCustom": "カスタム追加",
  "qual.negativeKarma": "不利から得られるカルマ {used}",
  "qual.career": "キャリア",
  "qual.metagenic": "メタジェネティック資質: 有利 {positive} ／ 不利 {negative}",
  "qual.metagenicLimit": " ／ 上限 {limit}",
  "qual.metagenicNoChangeling": "（Changeling 未取得）",
  "qual.metagenicUnbalanced": " ・ 収支が不均衡（不利＝有利 か 有利−1）",
  "qual.owned": "取得済み",
  "qual.positive": "有利な資質",
  "qual.negative": "不利な資質",
  "qual.karmaLabel": "カルマ",
  "qual.karmaBase": "（条件で変動・表では {base}）",
  "qual.freeAttached": " / 付帯（無料）",
  "qual.disabledBy": " / {ware} があるので無効",
  "qual.optionalPower": "任意パワーを選択",
  "qual.careerTaken": " / キャリアで取得（{cost}カルマ）",
  "qual.careerTakenNegative": " / キャリアで取得（カルマなし）",
  "qual.buyoffHint": " / 外すと買い戻し {cost}カルマ",
  "qual.careerPrice": " / キャリアでは {cost}カルマ",
  "qual.careerPriceNegative": " / キャリアではカルマなし",
  "qual.removed": "キャリアで外した資質",
  "qual.removedBuyoff": "買い戻し {cost}カルマ",
  "qual.removedPositive": "返金なし",
  "qual.restore": "戻す",
  "qual.restoreHint": "{name} を取り直して、キャリアで外す前に戻す",
  "qual.rebaseline": "今の資質を作成時のものとして扱う",
  "qual.rebaselineHint":
    "作成時のミスをキャリアで直したときに。キャリアでの取得・買い戻しの請求をすべて取り消します",
  "qual.rebaselineConfirm":
    "今の資質を作成時のものとして扱い、キャリアでの取得・買い戻しのカルマを取り消しますか？",
  "qual.attached": "付帯",
  "qual.empty": "まだありません。有利／不利で絞り込んで追加できます。",
  "qual.filter.positive": "有利",
  "qual.filter.negative": "不利",
  "qual.filter.metagenic": "メタジェネ",
  "qual.search": "資質を検索",
  "qual.taken": " / 取得{count}",
  "qual.level": "Lv",
  "qual.pickLevel": "{name}の取得Lv",
  "qual.ownedLevel": "{name}の所持Lv",
  "qual.maxLevel": " / 最大Lv{max}",
  "qual.changeLevel": "Lv変更",
  "qual.needsTarget": " / 対象が必要",
  "qual.wayExclusive": " / 他の Way と排他",
  "qual.replacesNote": " / 追加すると両立しない資質を外します",

  // --- quality target editors -------------------------------------------
  // One quality in ten needs a target chosen with it, and each kind asks a
  // different question. `QualityExtraEditor` branches on `extra_kind`.
  "qual.replace": "入れ替え",
  "quality.addSpirit": "追加精霊を選択",
  "quality.addSpiritN": "追加精霊 {index}を選択",
  "quality.marketCategory": "商品カテゴリーを選択",
  "quality.marketContact": "コンタクトを選択",
  "quality.marketBonus": "入手判定 +{bonus}（実効 Avail −{bonus}）",
  "quality.side": "左右を選択",
  "quality.matrixAction": "マトリックスアクションを選択",
  "quality.matrixActionFree": "マトリックスアクションを手入力",
  "quality.orType": "または手入力",
  "quality.expertise": "{skill} の Expertise を選択",
  "quality.expertiseAny": "Expertise を選択",
  "quality.expertiseFree": "Expertise を手入力",
  "quality.expertiseNote": "専門+3（無料）",
  "quality.weaponSkill": "技能を選択",
  "quality.spellCategory": "呪文カテゴリーを選択",
  "quality.spirit": "精霊を選択",
  "quality.attachedQuality": "付帯資質を選択",
  "quality.skillGroup": "技能グループを選択",
  "quality.attribute": "能力値を選択",
  "quality.target": "対象を選択",
  "quality.targetFree": "対象を手入力",

  // --- shared across the gear / catalog panels --------------------------
  "quality.targetPlaceholder": "内容を入力",
  // What each family of free-text quality is asking for. See
  // lib/character/quality-placeholder.ts for which quality maps to which.
  "quality.ph.addiction": "依存の対象（ノヴァコーク、BTL など）",
  "quality.ph.allergy": "アレルゲン（花粉、日光など）",
  "quality.ph.phobia": "恐怖の対象（高所、昆虫など）",
  "quality.ph.group": "相手の集団（メタ種族、企業、覚醒者など）",
  "quality.ph.code": "規範の内容",
  "quality.ph.dayJob": "勤め先と仕事の内容",
  "quality.ph.sinIssuer": "SIN の発行元（国家・企業名）",
  "quality.ph.rank": "所属組織と階級",
  "quality.ph.place": "場所",
  "quality.ph.compulsion": "衝動の内容",
  "quality.ph.brand": "メーカー名・製品名",
  "quality.ph.pursuer": "追う相手（人物・組織）",
  "qual.sharedLimit": " / {names} と合わせて最大{max}",
  "grade.label": "等級 {grade}",
  "grade.summary": "等級 {grade} ・ カルマ {karma}",
  "grade.karma": "{karma}カルマ",
  "grade.named": " ・ {name}",
  "grade.discount": "（{list} 割引）",

  "grade.discountHint": "各 −10%（累積で減算）",
  "contact.free": "無料枠 CHA×{mult} = {used}/{free}",
  "contact.over": " ・ 超過 {paid}点（{karma}カルマ）",
  "contact.minimum": "。コネ値と忠実値は最低1",
  "contact.careerCap": "。キャリアでは合計上限なし",
  "contact.chargenCap": "、作成時は合計7まで",
  "contact.perPoint": "。超過分は1点{karma}カルマです",
  "contact.perPointFree": "（Networker 等により無料）",
  "contact.points": "{points}点",
  "contact.group": " / グループ",
  "contact.billable": " / 課金 {points}点",
  "contact.connection": "コネ値",
  "contact.loyalty": "忠実値",
  "contact.name": "名前",
  "contact.role": "役割",

  "contact.roleOptional": "役割（任意）",
  "martial.styles": "流派 {styles}/{max}",
  "martial.techniques": " ・ 技 {used}/{max}",
  "martial.karma": " ・ カルマ {karma}",
  "martial.note":
    "（流派7カルマに技1つ込み、追加技は各5カルマ。作成時は流派1・技合計5まで。資質武道は流派枠外）",
  "martial.unarmedReach": " ・ 素手Reach +{reach}",
  "martial.freeQuality": " / 無料（資質）",
  "martial.cost": " / {karma}カルマ（流派 {style} + 追加技）",
  "martial.oneTech": " / 技1つのみ",
  "martial.techIncluded": " / 込み",
  "martial.search": "武道を検索",
  "martial.rowCost": "{karma}カルマ（技1込み）",
  "martial.techCount": "技 {count}種",
  "martial.specOptions": " / 専門化候補 {list}",
  "martial.owned": "取得済",
  "martial.capped": "上限",

  "martial.take": "取得",
  "prio.sumTotal": "合計 {used}/{max}",
  "prio.karmaNuyenRate": " ・ 1K={rate}¥（最大 {max}K）",
  "prio.leftoverToNuyen": "残カルマ→¥ 最大 {max}K",
  "prio.leftoverSlider": "残カルマ→新円（{k}K = {nuyen}¥）",
  "prio.karmaSlider": "カルマ→新円（{k}K = {nuyen}¥）",
  "prio.leftoverSliderLabel": "新円に回す残カルマ",
  "prio.cellHint": "{cat} を優先度 {letter} にする",
  "prio.cellSwapHint":
    "{cat} を優先度 {letter} にする（今そこを使っている {other} と入れ替わります）",
  "settings.folder": "スタイル一式を読み込む",
  "settings.folderHint":
    "settings と customdata が入ったフォルダごと選びます。中のセッティングは全部プルダウンに入り、選んだものに合わせてカスタムデータが結合されます。ファイルはこのブラウザに残り、サーバーには結合結果だけが一時的に置かれます",
  "settings.customDataFailed": "カスタムデータを読み込めませんでした。",
  "settings.zipNotAZip":
    "zip として読めませんでした。拡張子が .zip でも中身が壊れていることがあります。",
  "settings.zipUnsupported":
    "この zip は読めません（パスワード付き、ZIP64、または未対応の圧縮形式）。作り直すか、フォルダごと選んでください。",
  "settings.customDataNotAFolder":
    "個別のファイルではなく customdata フォルダ自体を選んでください（同じ名前のファイルが複数あり、どのフォルダのものか判別できません）。",
  "settings.customDataApplied": "カスタムデータを {count} 件適用しました",
  "settings.customDataSkipped": "未適用 {count} 件: {items}",
  "settings.customDataIgnored": "{files} はこの app が扱わないため対象外",
  "settings.mergeShow": "内訳を見る",
  "settings.mergeHide": "内訳を閉じる",
  "settings.mergeAdded": "追加",
  "settings.mergeRemoved": "削除",
  "settings.mergeEdited": "{fields} を変更",
  "settings.mergeCount": "{count} 件",
  "settings.mergeTruncated":
    "件数が多いため、内訳はここまでを表示しています（適用件数は上のとおり）。",
  "settings.customDataNeeded":
    "このセッティングはカスタムデータ（ハウスルール）を {count} 件参照しています。読み込むまで、そこでの追加・変更はいっさい効きません（素のデータで計算されます）。",
  "settings.customDataPick": "customdata ごと読み込む",
  "settings.customDataPickHint":
    "settings と customdata が並んでいるフォルダを、フォルダごと選びます。セッティングファイル単体ではカスタムデータは付いてきません",
  "settings.groupLoaded": "読み込んだファイル",
  "settings.groupShipped": "Chummer 同梱",
  "settings.load": "セッティングを読み込む",
  "settings.loadHint":
    "Chummer の settings フォルダにある .xml か、settings と customdata が入ったフォルダを固めた .zip を読み込みます。ファイルは送信されず、このブラウザにだけ残ります（zip はフォルダを選べない端末 ―― Android など ―― のための入口でもあります）",
  "settings.loadFailed": "セッティングファイルを読み込めませんでした。",
  "settings.forget": "このセッティングを削除",
  "settings.forgetHint": "{name} をこのブラウザから削除します（キャラクターは消えません）",
  "settings.knob.allowbiowaresuites":
    "バイオウェア・スイートの使用を認める（このアプリはスイートを扱わないので、まとめ買いの項目が出てきません）",
  "settings.knob.alloweditpartofbaseweapon":
    "武器アクセサリ・改造が元の武器の性能を書き換えてよい（Chummer の編集画面の設定）",
  "settings.knob.allowskilldicerolling":
    "ダイス・プールからダイスツールを起動できる（Chummer の操作設定）",
  "settings.knob.allowskillregrouping":
    "技能値がすべて同じなら能動技能を再びグループにまとめてよい（SR5 FAQ）",
  "settings.knob.armordegredation": "防具の劣化を適用する",
  "settings.knob.autobackstory": "バックストーリーを自動生成する（Chummer の操作設定）",
  "settings.knob.boundspiritexpression": "束縛できる精霊の数の式（能力値 1 つの形だけ扱えます）",
  "settings.knob.chargenkarmatonuyenexpression":
    "カルマ→新円の換算式（`{Karma} * 倍率 + {PriorityNuyen}` の形だけ扱えます）",
  "settings.knob.contactpointsexpression":
    "自由に使えるコンタクト・ポイントの式（`{CHAUnaug} * 倍率` の形だけ扱えます）",
  "settings.knob.cyberlimbattributebonuscapoverride":
    "サイバーリムの【筋力】【敏捷力】ボーナス上限を既定値から変える",
  "settings.knob.dicepenaltysustaining":
    "維持中の呪文・複合体 1 つあたりのダイス・ペナルティ（卓で処理する数値）",
  "settings.knob.enableenemytracking":
    "敵をコンタクトの一種として扱う（SR4 ルール。このアプリは敵を扱いません）",
  "settings.knob.enemykarmaqualitylimit":
    "敵で得たカルマを不利な資質の上限に数える（このアプリは敵を扱いません）",
  "settings.knob.essenceformat": "エッセンスの小数桁数（Chummer の表示設定）",
  "settings.knob.exceednegativequalitieslimit": "不利な資質を上限を超えて取ってもカルマは増えない",
  "settings.knob.extendanydetectionspell": "どの探知呪文でも超広域版として習得できる（SM179）",
  "settings.knob.karmacomplexformoption": "複合体オプションのカルマ（SR4 由来）",
  "settings.knob.karmacomplexformskillsoft": "複合体スキルソフトのカルマ（SR4 由来）",
  "settings.knob.karmacontact": "コンタクト 1 点あたりのカルマ",
  "settings.knob.karmaenemy": "敵 1 点あたりのカルマ（このアプリは敵を扱いません）",
  "settings.knob.karmaimprovecomplexform": "複合体のレーティングを上げるカルマ",
  "settings.knob.karmajoingroup": "魔法結社／ネットワークに加入するカルマ",
  "settings.knob.karmaleavegroup": "魔法結社／ネットワークから脱退するカルマ",
  "settings.knob.karmamaneuver": "Maneuver 1 つのカルマ（SR4 由来）",
  "settings.knob.karmametamagic":
    "追加メタマジック／エコーのカルマ（このアプリはイニシエート 1 段階につき 1 つだけ扱います）",
  "settings.knob.karmanewaiadvancedprogram": "AI の上級プログラム 1 つのカルマ",
  "settings.knob.karmanewaiprogram": "AI のプログラム 1 つのカルマ",
  "settings.knob.karmaquality": "資質 1 点あたりのカルマ",
  "settings.knob.karmaspiritfettering": "精霊の Fettering に払うフォース 1 点あたりのカルマ",
  "settings.knob.knowledgepointsexpression": "知識技能ポイントの式（能力値と四則演算だけ扱えます）",
  "settings.knob.morelethalgameplay": "よりデッドリーなプレイ（SR4 75）",
  "settings.knob.mysadeptsecondmagattribute":
    "Mystic Adept はパワーポイントの特別ルールの代わりに 2 つ目の【魔法】を使う",
  "settings.knob.nuyenformat": "新円の小数桁数（Chummer の表示設定）",
  "settings.knob.priorityspellsasadeptpowers":
    "【魔法】プライオリティの初期呪文をパワーポイントに回せる",
  "settings.knob.registeredspriteexpression":
    "登録できるスプライトの数の式（能力値 1 つの形だけ扱えます）",
  "settings.knob.reverseattributepriorityorder":
    "能力値はプライオリティ・ポイントより先にカルマで伸ばす",
  "settings.knob.specialkarmacostbasedonshownvalue":
    "特殊能力値（Mystic Adept のパワーポイントを含む）を伸ばすカルマは、エッセンス減少で割り引かれない",
  "settings.unsupportedHere":
    "このセッティングのハウスルール {count} 件は未対応です。この分の数値・選択肢は Chummer と食い違います:",
  "settings.unsupportedHarmless":
    "ほかに {count} 件、このアプリの計算に関係しない設定があります: {items}",
  "settings.preset": "セッティング",
  "settings.presetNone": "制限なし（全ルールブック）",
  "settings.presetHint": "Chummer 同梱のセッティング。使用ルールブックと作成方式が切り替わります",
  "settings.booksAll": "全ルールブックが対象",
  "settings.booksCount": "使用ルールブック {count} / {total}",
  "settings.custom": "カスタム",
  "settings.booksShow": "ルールブックを選ぶ",
  "settings.booksHide": "閉じる",
  "settings.booksAllOn": "全部オン",
  "settings.booksAllOnHint": "すべてのルールブックにチェックを入れます",
  "settings.booksAllOff": "全部オフ",
  "settings.booksAllOffHint": "基本ルールブック（SR5）だけを残して、ほかのチェックをすべて外します",
  "settings.booksHint": "購入できる項目をルールブックで絞り込みます",
  "settings.booksNote":
    "チェックを外したルールブックの項目は購入一覧に出なくなります。すでに所持している装備・資質は消えません。すべて外すと制限なしに戻ります。",
  "prio.methodPriorityHint": "標準の作成法。A〜E を 5 項目に 1 つずつ割り当てます（SR5 p.65）",
  "prio.methodSumHint":
    "同じ表を使い、A=4／B=3／C=2／D=1／E=0 の合計が 10 になるように選びます。重複可",
  "prio.methodKarmaHint": "優先度表を使わず、すべてを 800 カルマで購入します（SR5 p.94）",
  "prio.karmaSliderLabel": "新円に回すカルマ",
  "prio.nuyenSliderHint": "カルマ 1 点＝{rate}¥。作成中のみ交換でき、逆方向には戻せません",
  "prio.karmaNote":
    "優先度表は使いません。メタ／能力値／技能／術式などをカルマで購入します（開始 {pool}）。MAG／RES はタレント選択で解禁され、最低1から買い上げます。無料の術式枠はありません。",
  "prio.talent": "タレント",
  "prio.breakdownA":
    "内訳: メタ {meta} / 能力値 {attrs} / 技能 {skills} / 知識 {knowledge} / 専門化 {specs}",
  "prio.breakdownB": "資質 {qualities} / 新円交換 {nuyenKarma} / その他 {other}",
  "prio.sumHint":
    "同じ優先度を複数カテゴリーに割り当てできます。合計がちょうど 10 になるようにしてください。",

  "prio.priorityHint": "A〜E は各1回。クリックで入れ替えます。",
  "life.comforts": "快適さ +",
  "life.area": "地域 +",
  "life.security": "防犯 +",
  "life.raiseHint":
    "このライフスタイルの基本値から上げた段数。1 段ごとに LP 1 と、基本額の 10%（と、あればその段の値段）がかかります（RF p.219）。",
  "life.base": "基本 {cost}¥",
  "life.multiplier": " / 倍率 {pct}%",
  "life.qualityCost": " / 資質 +{cost}¥",
  "life.lpUsed": " / LP {used}/{max}",
  "life.lp": " / LP {lp}",
  "life.quality": "ライフスタイル資質",

  "life.freeGrids": " / 付属グリッド {count}",
  "attrs.wareBonus": " ウェア+{bonus}",
  "attrs.meat": " 肉{value}",
  "attrs.points": "能力値点 {used}/{max} ・ 特殊点 {specialUsed}/{specialMax}",
  "attrs.rowHint": "メタの下限 {min}／作成上限 {max}／増強込みの上限 {aug}",
  "attrs.karmaLevels": "うちカルマ",
  "attrs.karmaHint":
    "この能力値の上から何レベルをカルマで買ったか。その分は能力値点を使わず、上げた後の値×5 カルマかかります。",
  "attrs.karmaSpent": "カルマで上げた能力値：{karma} カルマ",
  "attrs.minNote":
    "各能力値はメタの最低値から始まります（オレンジの目盛り）。そこまでは無料で、能力値点を使うのは超えた分だけです。",

  // --- character sheet -----------------------------------------------------
  // Section headings. `Section` takes the key, not the sentence, so a section
  // cannot hard-code its own title.
  "attrs.replacedRanges":
    "能力値の上下限は {list} のものに置き換わっています（メタタイプのものではありません）。",
  "prio.cell.anyMetatype": "全てのメタタイプ",
  "prio.cell.humanDwarfElfOrkAi": "ドワーフ, オーク, エルフ, ヒューマン, or A.I.",
  "prio.cell.humanOrElf": "エルフ or ヒューマン",
  "prio.cell.human": "ヒューマン",
  "prio.cell.magicianOrTechnomancer": "魔法使い or テクノマンサー",
  "prio.cell.adeptMagicianTechnomancer": "アデプト, 魔法使い or テクノマンサー",
  // The talent dropdown's options. The catalog ships them pre-formatted
  // ("Magician - 6 Magic/10 Spells"), so the name and the ratings tail are
  // translated separately. Run Faster's talents (Apprentice, Aware, Enchanter,
  // Explorer) keep their English names, as its metavariants do.
  "prio.cell.adeptOrAspectedMagician": "アデプト or 偏位魔法使い",
  "talent.magician": "魔法使い",
  "talent.mysticAdept": "ミスティックアデプト",
  "talent.adept": "アデプト",
  "talent.aspectedMagician": "偏位魔法使い",
  "talent.technomancer": "テクノマンサー",
  "talent.mundane": "マンディン",
  "talent.magicSpells": "魔力{magic}/術式{spells}",
  "talent.magic": "魔力{magic}",
  "talent.resonanceForms": "共振力{resonance}/複合体{forms}",
  "prio.cell.attributes": "{points} ({special}) 能力値",
  // build-method buttons. "Sum to Ten" and "Karma" are kept as they read on
  // the sheet; only Priority had a settled Japanese label.
  "prio.cell.skills": "{skills} 技能/{groups} 技能グループ",
  "prio.method.priority": "優先度",
  "prio.method.sumToTen": "Sum to Ten",

  "prio.method.karma": "Karma",
  "prio.cat.heritage": "メタタイプ",
  "prio.cat.attributes": "能力値",
  "prio.cat.talent": "魔力/共振力",
  "prio.cat.skills": "技能",

  // --- lib/character/format.ts ---------------------------------------------
  "prio.cat.resources": "資金",
  "qual.blockPrereq": "前提を満たしていません",

  "qual.blockForbidden": "現在のキャラクターでは取れません",
} as const;
