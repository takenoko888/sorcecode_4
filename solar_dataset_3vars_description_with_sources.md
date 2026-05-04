# solar_dataset_3vars.csv 説明書（出典付き）

## 1. 対象CSV
- 対象ファイル: data/solar_dataset_3vars.csv
- 用途: グループワーク（ラッソ正則化を利用した基底展開法）
- 変数は3つのみ:
  - y: power_w [W]
  - x1: irradiance_wm2 [W/m^2]
  - x2: module_temp_c [degC]

## 2. このCSVをどう作ったか
このCSVは、既存の data/solar_dataset.csv から必要3列だけを抽出して作成した。

実行コマンド（PowerShell）:

```powershell
Import-Csv "data/solar_dataset.csv" |
  Select-Object power_w, irradiance_wm2, module_temp_c |
  Export-Csv "data/solar_dataset_3vars.csv" -NoTypeInformation -Encoding UTF8
```

## 3. 列の意味（3列のみ）
1. power_w
- 意味: 発電電力 [W]
- 由来: 生成元スクリプトの仕様では「実測があれば実測、なければ proxy」を採用。

2. irradiance_wm2
- 意味: 日射強度 [W/m^2]
- 由来: Open-Meteo の global_tilted_irradiance（あれば優先）または shortwave_radiation を使用。

3. module_temp_c
- 意味: モジュール温度 [degC]
- 由来: 周囲温度と日射から推定。

推定に使われる代表式（生成元スクリプト仕様）:
- module_temp = ambient + ((NOCT - 20) / 800) * irradiance
- temp_factor = max(0, 1 + temp_coeff_per_c * (module_temp - 25))
- power_proxy = panel_area * panel_efficiency * irradiance * temp_factor

## 4. 元データの由来
- 直接の元CSV: data/solar_dataset.csv
- その生成仕様: download_solar_dataset.py
- 元データ取得元サイト（公式）: https://open-meteo.com/
- 利用API: Open-Meteo Historical Weather API
- 実際の取得エンドポイント: https://archive-api.open-meteo.com/v1/archive

重要:
- 現在の data/solar_dataset.csv では power_source が全件 proxy（実測 power_w は未合流）。
- したがって、この data/solar_dataset_3vars.csv の power_w も実質的には proxy 由来。

## 5. 内容検証（作成時確認）
- source_row_count (data/solar_dataset.csv): 2631
- 3vars_row_count (data/solar_dataset_3vars.csv): 2631
- データの日付範囲（何日から何日まで）: 2025-04-01 から 2025-10-31
- source_timestamp_minmax: 2025-04-01 07:00:00 .. 2025-10-31 16:00:00
- source_power_source_counts: proxy=2631
- 3vars_headers_exact_required_order: True

## 6. 実習レポートにそのまま書ける要約
本実習では、data/solar_dataset.csv から power_w, irradiance_wm2, module_temp_c の3列のみを抽出した data/solar_dataset_3vars.csv を用いた。データの日付範囲は 2025-04-01 から 2025-10-31 である。説明変数は x1=irradiance_wm2, x2=module_temp_c、目的変数は y=power_w である。各変数定義とデータ生成ロジックは download_solar_dataset.py に基づき、3変数の採用理由は groupwork03_solar_data_guide.md の方針に基づいている。なお本CSVの power_w は全件 proxy 由来であり、実測電力を含める場合は measured-power CSV のマージが必要である。
