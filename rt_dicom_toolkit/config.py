"""
RT DICOM Toolkit の設定モジュール
"""

import os
from pathlib import Path

# アプリケーションのベースディレクトリ
BASE_DIR = Path(__file__).parent.parent.absolute()

# デフォルトのデータディレクトリ
DATA_DIR = Path(os.environ.get('RTDT_DATA_ROOT', BASE_DIR / 'data')).expanduser().absolute()

# デフォルトの入出力ディレクトリ
DEFAULT_INPUT_DIR = DATA_DIR / 'input_dicom'
DEFAULT_ANONYMOUS_DIR = DATA_DIR / 'anonymous_dicom'
DEFAULT_LOG_DIR = DATA_DIR / 'logs'
DEFAULT_REPORT_DIR = DATA_DIR / 'validation_reports'

# ディレクトリが存在しない場合は作成
DEFAULT_INPUT_DIR.mkdir(exist_ok=True, parents=True)
DEFAULT_ANONYMOUS_DIR.mkdir(exist_ok=True, parents=True)
DEFAULT_LOG_DIR.mkdir(exist_ok=True, parents=True)
DEFAULT_REPORT_DIR.mkdir(exist_ok=True, parents=True)

# ログ設定
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# 匿名化設定のデフォルト
DEFAULT_ANONYMIZATION_LEVEL = 'full'  # 'full' or 'partial'
DEFAULT_PRIVATE_TAGS_HANDLING = 'remove'  # 'remove' or 'keep'
DEFAULT_UID_HANDLING = 'consistent'  # 'consistent' or 'generate'
DEFAULT_KEEP_STRUCTURE = True
DEFAULT_PATIENT_ID_METHOD = 'hash'  # 'hash' or 'sequential'
