# Sleep Condition Controller

室温監視による睡眠時エアコン自動制御システム

## 概要

このプログラムは、夏の夜の睡眠時における省エネ型エアコン自動制御システムです。室温を監視し、設定した閾値を超えた場合のみエアコンを短時間運転（30分）することで、快適な睡眠環境を保ちながら消費電力を抑制します。Ambientに室温データが定期的にアップロードされていることが前提になります。

## 機能

- **温度監視**: Ambientサービスから最新の温度データを取得
- **自動エアコン制御**: 温度閾値に基づいてエアコンのON/OFF制御
- **タイマー機能**: エアコン起動から一定時間後の自動停止
- **実行制御**: settings.iniファイルによるプログラム実行の有効/無効制御
- **ログ出力**: システムログとコンソールへの詳細なログ出力

## 動作フロー

### 0. 実行制御チェック
- settings.iniファイルの`[enabled]`セクション`run`パラメータを確認
- `run = 0`の場合：プログラム終了
- `run = 1`の場合：以下の処理を継続

### 1. last_alert_timeが空の場合
- Ambientから温度データを取得
- 温度が閾値（デフォルト34℃）を超えている場合：
  - エアコンを起動
  - 現在時刻をlast_alert_timeに保存
- 閾値以下の場合：プログラム終了

### 2. last_alert_timeが存在する場合
- 前回のエアコン起動からの経過時間を確認
- チェック間隔（デフォルト30分）を超えている場合：
  - エアコンを停止
  - last_alert_timeをクリア
  - プログラム終了
- チェック間隔内の場合：プログラム終了

**特別な動作**: 設定された強制終了時間のcron実行時は、チェック間隔に関係なくエアコンを停止し、last_alert_timeをクリアします。

## 必要な環境

### システム要件
- Python 3.x
- Linux環境（syslog対応）

### Pythonライブラリ
```bash
pip install git+https://github.com/TakehikoShimojima/ambient-python-lib.git
pip install broadlink
```

### 外部ツール
- broadlink_cli: Broadlink社製IR学習リモコン制御用CLI
- Pythonのbroadlinkライブラリに含まれる

## 設定

### 1. Ambient設定
```python
AMBIENT_CHANNEL_ID = "your_channel_id"    # AmbientチャネルID
AMBIENT_WRITE_KEY = "your_write_key"      # Ambientライトキー
AMBIENT_READ_KEY = "your_read_key"        # Ambientリードキー
```

### 2. 温度閾値設定
```python
TEMPERATURE_THRESHOLD = 34.0  # 温度閾値（℃）
```

### 3. broadlink_cli設定
```python
BROADLINK_CLI_PATH = "/usr/local/bin/broadlink_cli"       # broadlink_cliのパス
EREMOTE_DEVICE_INFO = "/path/to/eremote_device_info"      # デバイス情報ファイル
AIRCON_START_IRCODE = "/path/to/aircon_start.ir"         # エアコン起動IRコード
AIRCON_STOP_IRCODE = "/path/to/aircon_stop.ir"           # エアコン停止IRコード
```

### 4. チェック間隔設定
```python
CHECK_INTERVAL = 1800  # 30分（秒単位）
```

### 5. 実行制御設定
```python
SETTINGS_FILE = "settings.ini"  # 設定ファイルパス
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
pip install ambient
```

### 3. broadlink_cliのインストール
Broadlink社製IR学習リモコンの制御に必要です。
```bash
# インストール方法は使用するデバイスに応じて異なります
```

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
# 1時〜8時まで5分間隔でチェック（温度監視とエアコン制御）
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

**注意**: 強制終了時間のcron実行時は、last_alert_timeが存在する場合（エアコンが稼動中の場合）、チェック間隔に関係なくエアコンを停止します。これにより、設定した起床時間にエアコンを確実に停止できます。

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
2024-07-03 15:30:02 - SleepCondition - INFO - 取得したデータ - 温度: 35.2℃
2024-07-03 15:30:02 - SleepCondition - INFO - 閾値を超えました - 温度: 35.2℃ (閾値: 34.0℃)
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

1. **Ambientからデータが取得できない**
   - チャネルID、ライトキー、リードキーの確認
   - ネットワーク接続の確認

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

## ライセンス

MIT License

## 作者

作成者名

## 更新履歴

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
