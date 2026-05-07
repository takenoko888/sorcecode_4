# solar_dataset_3vars.csv 説明書（出典付き）

## 1. 対象CSV
- 対象ファイル: data/solar_dataset_3vars.csv
- 用途: グループワーク（ラッソ正則化を利用した基底展開法）
- 変数は3つのみ:
  - y: power_w [W]
  - x1: irradiance_wm2 [W/m^2]
  - x2: module_temp_c [degC]

## 2. このCSVをどう作ったか
このCSVは、FMI（Finnish Meteorological Institute）が公開している太陽光発電実測データ `FMI_Helsinki_PV.csv` から、必要な3列だけを同じ形式に整形して作成した。

実行コマンド（PowerShell）:

```powershell
python build_fmi_solar_dataset.py
```

このスクリプトは `data/solar_dataset.csv`（詳細列あり）と `data/solar_dataset_3vars.csv`（3列のみ）を生成する。

## 3. 列の意味（3列のみ）
1. power_w
- 意味: 発電電力 [W]
- 由来: FMIデータの `pv_inv_out`
- 内容: インバータから系統へ出力された実測AC電力

2. irradiance_wm2
- 意味: 日射強度 [W/m^2]
- 由来: FMIデータの `GLOBA_PT1M_AVG(:31)`
- 内容: PVモジュール面に入射する実測日射量（plane-of-array irradiance）

3. module_temp_c
- 意味: モジュール温度 [degC]
- 由来: FMIデータの `TTECH_PT1M_AVG(:32)` と `TTECH_PT1M_AVG(:33)`
- 内容: 2点の実測モジュール温度の平均値

## 4. 元データの由来
- 直接の元CSV: FMI_Helsinki_PV.csv
- 元データ取得元: Finnish Meteorological Institute (FMI)
- データ公開ページ: https://fmi.b2share.csc.fi/records/fyyw1-16e65
- データセット名: PV production data with ancillary PV and meteorological data including solar radiation measurements from FMI's outdoor solar laboratories
- ライセンス: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 生成スクリプト: build_fmi_solar_dataset.py

重要:
- このCSVの `power_w`, `irradiance_wm2`, `module_temp_c` はすべて公開実測データ由来である。
- 以前の Open-Meteo 由来 proxy データではなく、FMI Helsinki Kumpula の実測PVデータに差し替えた。

## 5. 内容検証（作成時確認）
- source_row_count (data/solar_dataset.csv): 2631
- 3vars_row_count (data/solar_dataset_3vars.csv): 2631
- データの日付範囲（何日から何日まで）: 2016-06-10 から 2016-06-13
- source_timestamp_minmax: 2016-06-10 10:56:00 .. 2016-06-13 03:35:00
- source_power_source_counts: measured_pv_inv_out=2631
- 3vars_headers_exact_required_order: True
- 欠損値: power_w=0, irradiance_wm2=0, module_temp_c=0

## 6. 実習レポートにそのまま書ける要約
本実習では、FMI（Finnish Meteorological Institute）が公開している Helsinki Kumpula の太陽光発電実測データから、power_w, irradiance_wm2, module_temp_c の3列のみを抽出・整形した data/solar_dataset_3vars.csv を用いた。データの日付範囲は 2016-06-10 から 2016-06-13 であり、説明変数は x1=irradiance_wm2, x2=module_temp_c、目的変数は y=power_w である。power_w はインバータ出力の実測AC電力、irradiance_wm2 はPVモジュール面の日射量、module_temp_c は2点の実測モジュール温度の平均値である。
