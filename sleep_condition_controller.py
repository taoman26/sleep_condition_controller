#!/usr/bin/env python3

from ambient import Ambient
import json
import subprocess
import time
import logging
import logging.handlers
import os
import configparser
from datetime import datetime

# ログ設定
try:
    # syslogハンドラーを使用してシステムログに出力
    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_LOCAL0)
    syslog_handler.setFormatter(logging.Formatter('sleep_condition: %(levelname)s - %(message)s'))

    # コンソール出力用ハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # ロガーの設定
    logger = logging.getLogger("SleepCondition")
    logger.setLevel(logging.INFO)
    logger.addHandler(syslog_handler)
    logger.addHandler(console_handler)
    
except Exception as e:
    # syslogに接続できない場合は標準出力のみに出力
    print("システムログへの接続に失敗しました: {}".format(str(e)))
    print("標準出力のみにログを出力します")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger("SleepCondition")

# 設定パラメータ
# Ambient設定
AMBIENT_CHANNEL_ID = ""  # ここにあなたのAmbientのチャネルIDを設定
AMBIENT_WRITE_KEY = ""   # ここにあなたのAmbientのライトキーを設定
AMBIENT_READ_KEY = ""    # ここにあなたのAmbientのリードキーを設定

# 温度閾値
TEMPERATURE_THRESHOLD = 34.0  # 温度閾値（℃）

# broadlink_cli設定
BROADLINK_CLI_PATH = "/usr/local/bin/broadlink_cli"  # broadlink_cliのフルパス
EREMOTE_DEVICE_INFO = "/path/to/eremote_device_info"  # eRemoteデバイス情報のパス
AIRCON_START_IRCODE = "/path/to/aircon_start.ir"  # エアコン起動IRコードのパス
AIRCON_STOP_IRCODE = "/path/to/aircon_stop.ir"    # エアコン停止IRコードのパス

# チェック間隔（秒）- エアコン稼動時には30分ごとにチェック
CHECK_INTERVAL = 1800  # 30分（秒単位）

# 最後のアラート時間を保存するファイルパス
LAST_ALERT_TIME_FILE = "/tmp/sleep_condition_last_time.txt"

# 設定ファイルのパス
SETTINGS_FILE = "settings.ini"

def get_ambient_data():
    """
    Ambientから温度データを取得する関数（ambient-python-libを使用）
    """
    try:
        # ambient-python-libを使用してデータを取得
        ambient = Ambient(AMBIENT_CHANNEL_ID, AMBIENT_WRITE_KEY, AMBIENT_READ_KEY)
        data = ambient.read(n=1)  # 最新の1件のデータを取得
        
        if data and len(data) > 0:
            temperature = data[0].get('d1')  # d1が温度
            return temperature
        else:
            logger.error("Ambientからのデータが空です")
    except Exception as e:
        logger.error("データ取得中にエラーが発生しました: {}".format(str(e)))
    
    return None

def control_aircon(action):
    """
    broadlink_cliを使用してエアコンを制御する関数
    """
    try:
        # IRコードのパスから動作を判定
        if "start" in action.lower() or "on" in action.lower():
            action_name = "ON"
        elif "stop" in action.lower() or "off" in action.lower():
            action_name = "OFF"
        else:
            action_name = "不明"
        
        command = '{} --device @{} --send @{}'.format(BROADLINK_CLI_PATH, EREMOTE_DEVICE_INFO, action)
        
        logger.info("エアコン制御コマンドを実行: {}".format(command))
        logger.info("エアコンを{}にします".format(action_name))
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if result.returncode == 0:
            logger.info("エアコン制御({})に成功しました".format(action_name))
            return True
        else:
            logger.error("エアコン制御({})に失敗しました: {}".format(action_name, result.stderr))
            return False
    
    except Exception as e:
        logger.error("エアコン制御中にエラーが発生しました: {}".format(str(e)))
        return False

def check_and_control():
    """
    温度を確認し、閾値チェックとエアコン制御を行う
    """
    temperature = get_ambient_data()
    
    if temperature is None:
        logger.warning("温度データが取得できませんでした")
        return
    
    # settings.iniから温度閾値を取得
    temperature_threshold = get_temperature_threshold()
    
    logger.info("取得したデータ - 温度: {}℃".format(temperature))
    
    # 閾値を超えているか確認
    if temperature >= temperature_threshold:
        logger.info("閾値を超えました - 温度: {}℃ (閾値: {}℃)".format(temperature, temperature_threshold))
        # エアコンを起動
        if control_aircon(AIRCON_START_IRCODE):
            # last_alert_timeを現在の時間に更新
            save_last_alert_time(time.time())
    else:
        logger.info("閾値以下のため、プログラムを終了します")

def get_last_alert_time():
    """
    前回アラートを送信した時間を取得する関数
    """
    try:
        if os.path.exists(LAST_ALERT_TIME_FILE):
            with open(LAST_ALERT_TIME_FILE, 'r') as f:
                return float(f.read().strip())
        return 0
    except Exception as e:
        logger.error("前回のアラート時間の読み込みに失敗しました: {}".format(str(e)))
        return 0

def save_last_alert_time(timestamp):
    """
    アラートを送信した時間を保存する関数
    """
    try:
        with open(LAST_ALERT_TIME_FILE, 'w') as f:
            f.write(str(timestamp))
        logger.info("アラート時間を保存しました: {}".format(datetime.fromtimestamp(timestamp)))
    except Exception as e:
        logger.error("アラート時間の保存に失敗しました: {}".format(str(e)))

def clear_last_alert_time():
    """
    最後のアラート時間をクリアする関数
    """
    try:
        if os.path.exists(LAST_ALERT_TIME_FILE):
            os.remove(LAST_ALERT_TIME_FILE)
            logger.info("アラート時間をクリアしました")
    except Exception as e:
        logger.error("アラート時間のクリアに失敗しました: {}".format(str(e)))

def check_settings():
    """
    settings.iniファイルをチェックし、プログラムの実行可否を判定する関数
    """
    try:
        config = configparser.ConfigParser()
        
        # settings.iniファイルが存在しない場合はデフォルトで実行
        if not os.path.exists(SETTINGS_FILE):
            logger.warning("settings.iniファイルが見つかりません。デフォルトで実行します")
            return True
        
        # 設定ファイルを読み込み
        config.read(SETTINGS_FILE)
        
        # enabledセクションのrunパラメータを確認
        if config.has_section('enabled') and config.has_option('enabled', 'run'):
            run_value = config.get('enabled', 'run')
            if run_value == '1':
                logger.info("設定ファイル確認: プログラムの実行が有効です")
                return True
            elif run_value == '0':
                logger.info("設定ファイル確認: プログラムの実行が無効です")
                return False
            else:
                logger.warning("設定ファイルの値が不正です: {}. デフォルトで実行します".format(run_value))
                return True
        else:
            logger.warning("設定ファイルに必要なセクション/オプションが見つかりません。デフォルトで実行します")
            return True
            
    except Exception as e:
        logger.error("設定ファイルの読み込み中にエラーが発生しました: {}".format(str(e)))
        logger.info("デフォルトで実行します")
        return True

def get_force_stop_hour():
    """
    settings.iniファイルから強制終了時間を取得する関数
    """
    try:
        config = configparser.ConfigParser()
        
        # settings.iniファイルが存在しない場合はデフォルト値（9時）
        if not os.path.exists(SETTINGS_FILE):
            return 9
        
        # 設定ファイルを読み込み
        config.read(SETTINGS_FILE)
        
        # scheduleセクションのforce_stop_hourパラメータを確認
        if config.has_section('schedule') and config.has_option('schedule', 'force_stop_hour'):
            hour_value = config.get('schedule', 'force_stop_hour')
            try:
                hour = int(hour_value)
                if 0 <= hour <= 23:
                    return hour
                else:
                    logger.warning("強制終了時間が範囲外です: {}. デフォルト値（9時）を使用します".format(hour))
                    return 9
            except ValueError:
                logger.warning("強制終了時間の値が不正です: {}. デフォルト値（9時）を使用します".format(hour_value))
                return 9
        else:
            logger.info("強制終了時間が設定されていません。デフォルト値（9時）を使用します")
            return 9
            
    except Exception as e:
        logger.error("強制終了時間の読み込み中にエラーが発生しました: {}".format(str(e)))
        logger.info("デフォルト値（9時）を使用します")
        return 9

def get_temperature_threshold():
    """
    settings.iniファイルから温度閾値を取得する関数
    """
    try:
        config = configparser.ConfigParser()
        
        # settings.iniファイルが存在しない場合はデフォルト値（34.0℃）
        if not os.path.exists(SETTINGS_FILE):
            return 34.0
        
        # 設定ファイルを読み込み
        config.read(SETTINGS_FILE)
        
        # temperatureセクションのthresholdパラメータを確認
        if config.has_section('temperature') and config.has_option('temperature', 'threshold'):
            threshold_value = config.get('temperature', 'threshold')
            try:
                threshold = float(threshold_value)
                if threshold > 0:
                    return threshold
                else:
                    logger.warning("温度閾値が不正です: {}. デフォルト値（34.0℃）を使用します".format(threshold))
                    return 34.0
            except ValueError:
                logger.warning("温度閾値の値が不正です: {}. デフォルト値（34.0℃）を使用します".format(threshold_value))
                return 34.0
        else:
            logger.info("温度閾値が設定されていません。デフォルト値（34.0℃）を使用します")
            return 34.0
            
    except Exception as e:
        logger.error("温度閾値の読み込み中にエラーが発生しました: {}".format(str(e)))
        logger.info("デフォルト値（34.0℃）を使用します")
        return 34.0

def get_check_interval():
    """
    settings.iniファイルからチェック間隔を取得する関数
    """
    try:
        config = configparser.ConfigParser()
        
        # settings.iniファイルが存在しない場合はデフォルト値（1800秒 = 30分）
        if not os.path.exists(SETTINGS_FILE):
            return 1800
        
        # 設定ファイルを読み込み
        config.read(SETTINGS_FILE)
        
        # intervalsセクションのcheck_intervalパラメータを確認
        if config.has_section('intervals') and config.has_option('intervals', 'check_interval'):
            interval_value = config.get('intervals', 'check_interval')
            try:
                interval = int(interval_value)
                if interval > 0:
                    return interval
                else:
                    logger.warning("チェック間隔が不正です: {}. デフォルト値（1800秒）を使用します".format(interval))
                    return 1800
            except ValueError:
                logger.warning("チェック間隔の値が不正です: {}. デフォルト値（1800秒）を使用します".format(interval_value))
                return 1800
        else:
            logger.info("チェック間隔が設定されていません。デフォルト値（1800秒）を使用します")
            return 1800
            
    except Exception as e:
        logger.error("チェック間隔の読み込み中にエラーが発生しました: {}".format(str(e)))
        logger.info("デフォルト値（1800秒）を使用します")
        return 1800

def main():
    """
    メイン関数
    """
    logger.info("エアコン制御プログラムを開始します")
    
    # settings.iniファイルをチェック
    if not check_settings():
        logger.info("設定により実行が無効化されています。プログラムを終了します")
        return
    
    # 設定情報の確認
    if not AMBIENT_CHANNEL_ID or not AMBIENT_READ_KEY:
        logger.error("Ambient設定が不完全です。AMBIENT_CHANNEL_IDとAMBIENT_READ_KEYを設定してください。")
        return
    
    try:
        # 現在時刻を取得
        current_time = time.time()
        current_hour = datetime.fromtimestamp(current_time).hour
        
        # 強制終了時間を取得
        force_stop_hour = get_force_stop_hour()
        
        # settings.iniからチェック間隔を取得
        check_interval = get_check_interval()
        
        # last_alert_timeの状態を確認
        last_alert_time = get_last_alert_time()
        
        # 強制終了時間の場合は強制的にエアコンを停止
        if current_hour == force_stop_hour and last_alert_time > 0:
            logger.info("強制終了時間({}時)になりました。エアコンを強制停止します".format(force_stop_hour))
            clear_last_alert_time()
            control_aircon(AIRCON_STOP_IRCODE)
            logger.info("プログラムが正常に終了しました")
            return
        
        if last_alert_time == 0:
            # last_alert_timeが空（ファイルが存在しないか0）の場合
            logger.info("last_alert_timeが空です。温度チェックとエアコン制御を実行します")
            check_and_control()
        else:
            # last_alert_timeが空でない場合
            last_time_str = datetime.fromtimestamp(last_alert_time).strftime('%Y-%m-%d %H:%M:%S')
            logger.info("前回のアラート時間: {}".format(last_time_str))
            
            # 前回のアラートからの経過時間を確認
            elapsed_time = current_time - last_alert_time
            
            if elapsed_time >= check_interval:
                # チェック間隔を超えている場合
                logger.info("前回のアラートから{:.1f}分経過しました。エアコンを停止します".format(elapsed_time/60))
                
                # last_alert_timeをクリア
                clear_last_alert_time()
                
                # broadlink_cliでエアコンを停止
                control_aircon(AIRCON_STOP_IRCODE)
            else:
                # チェック間隔内の場合
                remaining_time = check_interval - elapsed_time
                logger.info("前回のアラートから{:.1f}分経過。次回チェックまで{:.1f}分".format(elapsed_time/60, remaining_time/60))
        
        logger.info("プログラムが正常に終了しました")
    except Exception as e:
        logger.error("予期せぬエラーが発生しました: {}".format(str(e)))

if __name__ == "__main__":
    main()