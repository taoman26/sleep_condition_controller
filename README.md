# Sleep Condition Controller

室温・湿度監視による睡眠時エアコン自動制御システム

## 概要

このプログラムは、夏の夜の睡眠時における省エネ型エアコン自動制御システムです。室温と湿度から算出した**不快指数（DI）**を監視し、ON閾値を超えたときのみエアコンを起動、OFF閾値まで下がったら停止するヒステリシス制御を行うことで、快適な睡眠環境を保ちながら消費電力を抑制します。制御には赤外線学習リモコンのeRemoteを使用します。また、ThingSpeakに温度・湿度データが定期的にアップロードされていることが前提になります。

## 機能

- **温度・湿度監視**: ThingSpeakサービスから最新の温度・湿度データを取得
- **不快指数によるスマート制御**: 温度と湿度から不快指数を算出し、ON/OFFで異なる閾値によるヒステリシス制御でエアコンをON/OFF
- **安全装置**: 不快指数が下がらない場合でも、最大稼働時間を超えたら強制的にエアコンを停止
- **実行制御**: settings.iniファイルによるプログラム実行の有効/無効制御
- **ログ出力**: システムログとコンソールへの詳細なログ出力

## 不快指数（DI）について

温度(T, ℃)と湿度(H, %)から以下の式で算出します。

```
DI = 0.81T + 0.01H(0.99T - 14.3) + 46.3
```

| DI | 体感 |
|---|---|
| 75未満 | やや暑い程度 |
| 75〜80 | 暑くて汗が出る |
| 80〜85 | 暑くてたまらない |
| 85以上 | 暑くて危険 |

ON閾値とOFF閾値を同じ値にすると、停止直後にすぐ再起動してしまう（ハンチング）ため、OFF閾値はON閾値より3〜5ポイント低い値を設定することを推奨します（デフォルト: ON=80.0, OFF=75.0）。

## 動作フロー

### 0. 実行制御チェック
- settings.iniファイルの`[enabled]`セクション`run`パラメータを確認
- `run = 0`の場合：プログラム終了
- `run = 1`の場合：以下の処理を継続

### 1. last_alert_timeが空（エアコン停止中）の場合
- ThingSpeakから温度・湿度を取得し、不快指数を算出
- 不快指数がON閾値（デフォルト80.0）以上の場合：
  - エアコンを起動
  - 現在時刻をlast_alert_timeに保存
- ON閾値未満の場合：プログラム終了

### 2. last_alert_timeが存在する（エアコン稼働中）場合
- ThingSpeakから温度・湿度を取得し、不快指数を算出
- 不快指数がOFF閾値（デフォルト75.0）以下に下がった場合：
  - エアコンを停止
  - last_alert_timeをクリア
- OFF閾値まで下がっていないが、稼働開始からの経過時間が最大稼働時間（安全装置、デフォルト30分）を超えた場合：
  - エアコンを強制停止
  - last_alert_timeをクリア
- それ以外（不快指数がOFF閾値より高く、最大稼働時間内）の場合：稼働を継続してプログラム終了

**特別な動作**: 設定された強制終了時間のcron実行時は、不快指数や経過時間に関係なくエアコンを停止し、last_alert_timeをクリアします。

## 必要な環境

### システム要件
- Python 3.5.3以降（Python 3.5.3〜3.12で動作確認済み）
- Linux環境（syslog対応）

### Pythonライブラリ
```bash
pip install broadlink
```
ThingSpeakへのデータ取得はPython標準ライブラリ（`urllib`）のみを使用しているため、追加のライブラリは不要です。

### 外部ツール
- broadlink_cli: Broadlink社製IR学習リモコン制御用CLI
- Pythonのbroadlinkライブラリに含まれる

## 設定

### 1. ThingSpeak設定
```python
THINGSPEAK_CHANNEL_ID = "your_channel_id"        # ThingSpeakチャネルID
THINGSPEAK_READ_API_KEY = "your_read_api_key"    # ThingSpeakリードAPIキー
```
ThingSpeakのチャネルには、field1に温度、field2に湿度のデータが定期的にアップロードされている必要があります。

### 2. 不快指数閾値設定
settings.iniファイルで設定します：
```ini
[discomfort_index]
on_threshold = 80.0   # この値以上でエアコンを起動します
off_threshold = 75.0  # この値以下でエアコンを停止します
```

### 3. broadlink_cli設定
```python
BROADLINK_CLI_PATH = "/usr/local/bin/broadlink_cli"       # broadlink_cliのパス
EREMOTE_DEVICE_INFO = "/path/to/eremote_device_info"      # デバイス情報ファイル
AIRCON_START_IRCODE = "/path/to/aircon_start.ir"         # エアコン起動IRコード
AIRCON_STOP_IRCODE = "/path/to/aircon_stop.ir"           # エアコン停止IRコード
```

### 4. 安全装置（最大稼働時間）設定
settings.iniファイルで設定します：
```ini
[safety]
max_runtime = 1800  # 30分（秒単位）。不快指数が下がらなくてもこの時間で強制停止
```

### 5. 実行制御設定
```python
SETTINGS_FILE = "/path/to/settings.ini"  # 設定ファイルのフルパス
```

### 6. スケジュール設定
強制終了時間はsettings.iniファイルで設定します：
```ini
[schedule]
force_stop_hour = 9  # 強制終了時間（0-23の24時間制）
```

## インストールと設定

### 1. リポジトリのクローン
```bash
git clone <repository_url>
cd sleep_condition_controller
```

### 2. 依存関係のインストール
```bash
pip install broadlink
```

### 3. broadlink_cliで情報を取得
Broadlink社製IR学習リモコンの制御に必要です。
Pythonのbroadlinkライブラリに含まれますので、インストール後にbroadlink_cliコマンドを使用して、以下の情報を取得してください。broadlink_cliの使い方はコマンドのヘルプを参照してください。
- broadlink_cliのフルパス
- eRemoteのデバイス情報
- お使いのエアコンの起動IRコード
- お使いのエアコンの停止IRコード

### 4. 設定ファイルの編集
`sleep_condition_controller.py`内の設定パラメータを環境に合わせて変更してください。

### 5. IRコードの準備
エアコンの起動・停止用IRコードファイルを準備し、パスを設定してください。

### 6. 実行制御設定ファイルの作成
`settings.ini`ファイルを作成し、プログラムの実行制御を設定してください。
```ini
[enabled]
# プログラムの実行制御
# 1: 実行する
# 0: 実行しない
run = 1

[schedule]
# 強制終了時間（24時間制）
# エアコンが稼動中の場合、この時間になったら強制的に停止する
force_stop_hour = 9

[discomfort_index]
# 不快指数（DI = 0.81T + 0.01H(0.99T-14.3) + 46.3）
# on_threshold以上でエアコンを起動し、off_threshold以下で停止します
on_threshold = 80.0
off_threshold = 75.0

[safety]
# 安全装置（秒）
# 不快指数がoff_thresholdまで下がらなくても、この時間を超えたら強制的に停止します
max_runtime = 1800
```

## 使用方法

### プログラム実行制御
settings.iniファイルでプログラムの実行を制御できます：

#### プログラムを有効にする
```ini
[enabled]
run = 1
```

#### プログラムを無効にする
```ini
[enabled]
run = 0
```

### 手動実行
```bash
python3 sleep_condition_controller.py
```

### cron設定例（睡眠時間中の1時〜9時に実行）
```bash
# 1時〜8時まで5分間隔でチェック（不快指数監視とエアコン制御）
*/5 1-8 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py

# 9時に1回実行（エアコン稼動中の場合は強制停止）
0 9 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py
```

**重要**: 強制終了時間を変更した場合は、cronの設定も合わせて変更する必要があります。

#### 強制終了時間が7時の場合の例
```bash
# 1時〜6時まで5分間隔でチェック
*/5 1-6 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py

# 7時に1回実行（強制停止）
0 7 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py
```

#### 強制終了時間が10時の場合の例
```bash
# 1時〜9時まで5分間隔でチェック
*/5 1-9 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py

# 10時に1回実行（強制停止）
0 10 * * * /usr/bin/python3 /path/to/sleep_condition_controller.py
```

**注意**: 強制終了時間のcron実行時は、last_alert_timeが存在する場合（エアコンが稼動中の場合）、不快指数や経過時間に関係なくエアコンを停止します。これにより、設定した起床時間にエアコンを確実に停止できます。

## ログ出力

### システムログ
- syslog（LOG_LOCAL0）に出力
- ログレベル: INFO

### コンソール出力
- 標準出力にも同時出力
- 実行状況の確認が可能

### ログ例
```
2024-07-03 15:30:01 - SleepCondition - INFO - エアコン制御プログラムを開始します
2024-07-03 15:30:01 - SleepCondition - INFO - 設定ファイル確認: プログラムの実行が有効です
2024-07-03 15:30:02 - SleepCondition - INFO - 取得したデータ - 温度: 29.5℃, 湿度: 70%, 不快指数: 80.3
2024-07-03 15:30:02 - SleepCondition - INFO - 不快指数がON閾値を超えました - 80.3 (ON閾値: 80.0)
2024-07-03 15:30:02 - SleepCondition - INFO - エアコンをONにします
2024-07-03 15:30:03 - SleepCondition - INFO - エアコン制御(ON)に成功しました
```

#### プログラム無効時のログ例
```
2024-07-03 15:30:01 - SleepCondition - INFO - エアコン制御プログラムを開始します
2024-07-03 15:30:01 - SleepCondition - INFO - 設定ファイル確認: プログラムの実行が無効です
2024-07-03 15:30:01 - SleepCondition - INFO - 設定により実行が無効化されています。プログラムを終了します
```

#### 9時の強制停止ログ例
```
2024-07-03 09:00:01 - SleepCondition - INFO - エアコン制御プログラムを開始します
2024-07-03 09:00:01 - SleepCondition - INFO - 設定ファイル確認: プログラムの実行が有効です
2024-07-03 09:00:01 - SleepCondition - INFO - 強制終了時間(9時)になりました。エアコンを強制停止します
2024-07-03 09:00:01 - SleepCondition - INFO - エアコンをOFFにします
2024-07-03 09:00:02 - SleepCondition - INFO - エアコン制御(OFF)に成功しました
2024-07-03 09:00:02 - SleepCondition - INFO - プログラムが正常に終了しました
```

## ファイル構成

```
sleep_condition_controller/
├── sleep_condition_controller.py  # メインプログラム
├── settings.ini                   # 実行制御設定ファイル
├── README.md                      # このファイル
└── /tmp/sleep_condition_last_time.txt  # 最後のアラート時間（自動生成）
```

## トラブルシューティング

### よくある問題

1. **ThingSpeakからデータが取得できない**
   - チャネルID、リードAPIキーの確認
   - ネットワーク接続の確認
   - 温度（field1）だけでなく湿度（field2）もセンサーから送信されているか確認（湿度が無いと不快指数が計算できません）

2. **broadlink_cliが動作しない**
   - パスの確認
   - デバイス情報ファイルの確認
   - IRコードファイルの存在確認

3. **syslogに出力されない**
   - `/dev/log`の存在確認
   - ログ権限の確認

4. **プログラムが実行されない**
   - settings.iniファイルの`run`パラメータを確認
   - `run = 1`に設定されているか確認

5. **強制終了時間が正しく動作しない**
   - settings.iniファイルの`force_stop_hour`パラメータを確認
   - 0-23の範囲で設定されているか確認
   - cronの設定時間と一致しているか確認

### デバッグ方法
- コンソール出力でリアルタイムログを確認
- 手動実行でエラー内容を確認

## Python バージョン互換性

このプログラムは **Python 3.5.3以降** で動作します。

### サポート対象
- **Python 3.5.3〜3.12**: 完全サポート
- **推奨バージョン**: Python 3.8以降（セキュリティサポート継続中）

### 使用している機能とバージョン要件
- `subprocess.run()`: Python 3.5以降
- `.format()` 文字列フォーマット: Python 3.0以降
- `configparser`: Python 3.0以降（標準ライブラリ）
- その他の標準ライブラリ: すべて古いバージョンから利用可能

### 注意事項
- f-string (`f"文字列 {変数}"`) は使用していないため、Python 3.5.3でも動作
- `capture_output`パラメータは使用せず、`stdout=subprocess.PIPE`を使用
- `text`パラメータは使用せず、`universal_newlines=True`を使用

## ライセンス

MIT License

## 作者

Michihiko Mikami

## 更新履歴

- v1.4.0: データ取得元をThingSpeakに変更
  - AmbientからThingSpeakへ移行（field1=温度、field2=湿度）
  - 外部ライブラリ（ambient-python-lib）への依存を廃止し、標準ライブラリのみでデータ取得
- v1.3.0: 不快指数によるスマート制御に変更
  - 温度単独の閾値制御から、温度・湿度から算出した不快指数によるヒステリシス制御（ON/OFF閾値）に変更
  - 固定タイマー方式を廃止し、不快指数がOFF閾値まで下がったら停止する方式に変更
  - 従来のチェック間隔（intervals.check_interval）は、不快指数が下がらない場合の安全装置（safety.max_runtime）として再定義
- v1.2.1: broadlink_cliの使い方の記載を修正
- v1.2.0: 強制終了時間の設定機能追加
  - settings.iniで強制終了時間を設定可能
  - cronの設定例を複数のパターンで記載
- v1.1.0: 実行制御機能追加
  - settings.iniファイルによるプログラム実行制御
  - 設定ファイルの動的読み込み
- v1.0.0: 初期リリース
  - 基本的な温度監視とエアコン制御機能
  - Ambientサービス連携
  - broadlink_cli連携
