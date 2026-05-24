# occto_tohoku_2025-07.csv 説明書（出典付き）

## 1. 対象CSV
- 東北エリアの電力需要（消費側）OCCTO公表の需給実績（速報・推計を含む可能性）
- 対象ファイル: data/occto_tohoku_2025-07.csv
- 用途: 実験IV-2（時系列解析/カルマンフィルタ長期予測）
- 変数は2つのみ:
  - t: timestamp (JST)
  - y: area_demand_mw [MW]（東北エリア需要）

## 2. このCSVをどう作ったか
OCCTOの広域予備率Web公表システムからCSVを取得し、東北エリアのみ抽出して t,y の2列に整形した。

取得URL（2025/07/01〜2025/07/31）:
https://web-kohyo.occto.or.jp/kks-web-public/download/downloadCsv?jhSybt=02&tgtYmdFrom=2025/07/01&tgtYmdTo=2025/07/31

整形手順:
1. CSVをダウンロード
2. エリア名 == "東北" の行のみ抽出
3. 「対象年月日」+「時刻」を t (JST) に変換
4. 「エリア需要(MW)」を y に採用
5. t,y のみ残して時刻順に並べ替え

## 3. 列の意味（2列のみ）
1. t
- 意味: 時刻 (JST), 30分刻み
- 由来: OCCTO CSV の「対象年月日」「時刻」

2. y
- 意味: 東北エリア需要 [MW]
- 由来: OCCTO CSV の「エリア需要(MW)」

## 4. 元データの由来
- 元データ取得元: 電力広域的運営推進機関 (OCCTO)
- 公開ページ: https://web-kohyo.occto.or.jp/kks-web-public/download/
- 情報種別: 広域予備率ブロック情報(翌日・当日) (jhSybt=02)
- 利用条件: OCCTO公開ページの利用規約に従うこと

## 5. 内容検証（作成時確認）
- row_count: 1457
- timestamp_minmax: 2025-07-01 00:30:00 .. 2025-07-31 23:30:00
- time_step: 30 minutes
- 欠損値: なし（t,y の欠損行は削除済み）

## 6. 実習レポートにそのまま書ける要約
本実習では、OCCTOの広域予備率Web公表システムで公開されている広域予備率ブロック情報(翌日・当日)のCSVから、東北エリアのエリア需要(MW)を抽出し、t,yの2列に整形した data/occto_tohoku_2025-07.csv を用いた。期間は 2025-07-01 00:30 から 2025-07-31 23:30 (JST) で、30分刻みの時系列データである。t は時刻、y は東北エリア需要(MW)を表す。
