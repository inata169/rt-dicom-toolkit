"""
DICOM匿名化の中核機能を提供するモジュール
"""

import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
import logging
import traceback
import threading

import pydicom
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
from pydicom.dataset import FileMetaDataset

from ..config import (
    DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_LOG_DIR,
    DEFAULT_ANONYMIZATION_LEVEL, DEFAULT_PRIVATE_TAGS_HANDLING, 
    DEFAULT_UID_HANDLING, DEFAULT_KEEP_STRUCTURE, DEFAULT_PATIENT_ID_METHOD
)
from .profiles import get_anonymization_profile
from ..utils.logging_utils import setup_logger
from ..utils.file_utils import find_dicom_files

class RTDicomAnonymizer:
    """放射線治療用DICOMファイルの匿名化を行うクラス"""
    
    def __init__(self, root=None):
        """
        初期化
        
        Args:
            root: GUIのルートウィンドウ（TkinterのRoot）、CLIモードの場合はNone
        """
        self.root = root
        
        # ディレクトリ設定
        self.input_dir = DEFAULT_INPUT_DIR
        self.output_dir = DEFAULT_ANONYMOUS_DIR
        self.log_dir = DEFAULT_LOG_DIR
        
        # 匿名化設定
        self.anonymization_level = DEFAULT_ANONYMIZATION_LEVEL
        self.private_tags = DEFAULT_PRIVATE_TAGS_HANDLING
        self.uid_handling = DEFAULT_UID_HANDLING
        self.keep_structure = DEFAULT_KEEP_STRUCTURE
        self.patient_id_method = DEFAULT_PATIENT_ID_METHOD
        
        # 状態管理
        self.patient_id_map = {}
        self.next_patient_id = 9000001
        self.uid_map = {}
        
        # ロガーの設定
        self.logger = setup_logger("RTDicomAnonymizer")
        
        # GUI関連の属性
        if self.root:
            self.log_text = None
            self.progress_var = None
            self.status_var = None
            
        self.log_message("匿名化ツール初期化完了")
        self.log_message(f"入力ディレクトリ初期設定: {self.input_dir}")
        self.log_message(f"出力ディレクトリ初期設定: {self.output_dir}")
        self.log_message(f"ログディレクトリ初期設定: {self.log_dir}")
    
    def log_message(self, message):
        """ログメッセージを表示とロガーに出力"""
        try:
            if self.root and hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.root.update_idletasks()
            
            # 常にコンソールにもログを出力
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"ログ出力エラー: {str(e)}")
    
    def generate_anonymous_id(self, original_id):
        """
        オリジナルの患者IDから匿名化IDを生成する
        
        Args:
            original_id: 元の患者ID
            
        Returns:
            匿名化された患者ID
        """
        # すでに変換済みの場合はそれを返す
        if str(original_id) in self.patient_id_map:
            return self.patient_id_map[str(original_id)]
        
        if self.patient_id_method == "sequential":
            if not hasattr(self, 'patient_counter'):
                self.patient_counter = 0
            self.patient_counter += 1
            new_id = f"Patient_{self.patient_counter:03d}"
        else:
            # 次の連番IDを生成（9000001からスタート）
            if self.next_patient_id > 9999999:
                # ID枯渇した場合のハッシュ処理
                hash_id = int(hashlib.md5(str(original_id).encode()).hexdigest(), 16) % 1000000
                new_id = f"9{hash_id:06d}"
            else:
                new_id = str(self.next_patient_id)
                self.next_patient_id += 1
            
        # マッピングを保存
        self.patient_id_map[str(original_id)] = new_id
        
        return new_id
    
    def get_modified_anonymization_profile(self):
        """現在の設定に基づいた匿名化プロファイルを取得"""
        # 基本プロファイルを取得
        profile = get_anonymization_profile(self)
        
        # 匿名化レベルに応じた調整
        if self.anonymization_level == "partial":
            # 日付と施設情報を保持する場合
            for key in ["StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
                       "StudyTime", "SeriesTime", "AcquisitionTime", "ContentTime",
                       "InstitutionName", "StationName"]:
                if key in profile:
                    del profile[key]
        
        # UID処理の調整
        if self.uid_handling == "consistent":
            # 一貫性を保つためのUID管理（self.uid_mapを使用）
            for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"]:
                if uid_tag in profile:
                    profile[uid_tag] = lambda x, tag=uid_tag: self.uid_map.setdefault(
                        f"{tag}_{str(x)}", generate_uid())
        
        return profile
    
    def anonymize_dicom(self, dcm, anonymization_profile, remove_private_tags=True):
        """
        DICOMファイルを匿名化する
        
        Args:
            dcm: 匿名化するDICOMデータセット
            anonymization_profile: 匿名化プロファイル
            remove_private_tags: プライベートタグを削除するかどうか
            
        Returns:
            変更されたタグとその値のディクショナリ
        """
        self.log_message(f"匿名化処理を開始: {dcm.filename if hasattr(dcm, 'filename') else 'Unknown'}")
        changes = {}
        
        # プライベートタグの処理
        if remove_private_tags:
            def remove_private_tags_recursive(dataset):
                count = 0
                private_tags = [tag for tag in dataset.keys() if tag.is_private]
                for tag in private_tags:
                    try:
                        del dataset[tag]
                        count += 1
                    except Exception as e:
                        self.logger.warning(f"プライベートタグ {tag} の削除中にエラー: {e}")
                
                # シーケンス内の各アイテムを再帰的に処理
                for elem in dataset.values():
                    if elem.VR == "SQ" and elem.value:
                        for item in elem.value:
                            if item is not None:
                                count += remove_private_tags_recursive(item)
                return count
            
            removed_count = remove_private_tags_recursive(dcm)
            self.log_message(f"{removed_count}個のプライベートタグを削除しました")
        
        # 匿名化プロファイルに従ってタグを処理
        processed_tags = 0
        for tag_name, replacement in anonymization_profile.items():
            # タグが存在するか確認
            if hasattr(dcm, tag_name):
                try:
                    original_value = getattr(dcm, tag_name)
                    
                    # 置換値が関数の場合は実行し、そうでない場合はそのまま使用
                    if callable(replacement):
                        try:
                            new_value = replacement(original_value)
                        except Exception as e:
                            self.logger.warning(f"タグ {tag_name} の処理中にエラーが発生: {e}")
                            continue
                    else:
                        new_value = replacement
                    
                    # 値を設定
                    try:
                        setattr(dcm, tag_name, new_value)
                        changes[tag_name] = {
                            "元の値": str(original_value),
                            "変更後の値": str(new_value)
                        }
                        processed_tags += 1
                    except Exception as e:
                        self.logger.warning(f"タグ {tag_name} の値設定中にエラーが発生: {e}")
                except Exception as e:
                    self.logger.warning(f"タグ {tag_name} の処理中にエラーが発生: {e}")
        
        self.log_message(f"{processed_tags}個のタグを匿名化しました")
        return changes
    
    def process_directory(self):
        """
        指定されたディレクトリ内のDICOMファイルを全て匿名化する
        """
        try:
            self.log_message("処理を開始します...")
            
            # 設定値を確認
            input_dir = self.input_dir
            output_dir = self.output_dir
            log_dir = self.log_dir
            keep_structure = self.keep_structure
            remove_private_tags = self.private_tags == "remove"
            
            # ディレクトリの存在確認
            if not input_dir.exists():
                error_msg = f"入力ディレクトリが存在しません: {input_dir}"
                self.log_message(error_msg)
                return
                
            self.log_message(f"入力ディレクトリ: {input_dir}")
            self.log_message(f"出力ディレクトリ: {output_dir}")
            self.log_message(f"ログディレクトリ: {log_dir}")
            
            # 出力ディレクトリとログディレクトリが存在しない場合は作成
            output_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)
            
            # UID対応マップと患者IDマッピングの初期化
            self.uid_map = {}
            self.patient_id_map = {}
            self.patient_counter = 0
            
            # ログファイルのパスを設定
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"rt_anonymization_log_{timestamp}.txt"
            summary_path = log_dir / f"rt_anonymization_summary_{timestamp}.json"
            
            # ファイルハンドラーをロガーに追加
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # 処理サマリー
            summary = {
                "処理開始時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "処理ファイル数": 0,
                "成功": 0,
                "スキップ": 0,
                "エラー": 0,
                "ファイル詳細": [],
                "患者ID対応表": {}
            }
            
            # ファイルリストの取得
            dicom_files = find_dicom_files(input_dir)
            total_files = len(dicom_files)
            self.log_message(f"検索完了: {total_files}ファイルが見つかりました")
            
            if total_files == 0:
                self.log_message("処理対象のファイルが見つかりません。")
                return
            
            # 匿名化プロファイルを取得
            anonymization_profile = self.get_modified_anonymization_profile()
            self.log_message("匿名化プロファイルを設定しました")
            
            # 入力ディレクトリ内のファイルを処理
            for i, file_path in enumerate(dicom_files):
                summary["処理ファイル数"] += 1
                
                # 進捗状況を更新
                progress = (i + 1) / total_files * 100
                if self.root and hasattr(self, 'progress_var') and self.progress_var:
                    self.progress_var.set(progress)
                    self.status_var.set(f"処理中... {i+1}/{total_files} ({progress:.1f}%)")
                
                self.log_message(f"処理中 ({i+1}/{total_files}): {file_path.name}")
                
                try:
                    # DICOMファイルとして読み込み
                    try:
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        
                        # ファイルの種類を特定
                        modality = "Unknown"
                        file_type = "Unknown"
                        if hasattr(dcm, 'Modality'):
                            modality = dcm.Modality
                            if modality == "RTPLAN":
                                file_type = "放射線治療計画"
                            elif modality == "RTDOSE":
                                file_type = "線量分布"
                            elif modality == "RTSTRUCT":
                                file_type = "臓器輪郭"
                            elif modality == "CT" or modality == "RTIMAGE":
                                file_type = "CT画像"
                        
                        self.log_message(f"ファイル種類: {file_type} (モダリティ: {modality})")
                        
                        # 出力ファイルパスを生成
                        if keep_structure:
                            # 元のディレクトリ構造を保持
                            rel_path = file_path.relative_to(input_dir)
                            output_path = output_dir / rel_path
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                        else:
                            # フラットなディレクトリ構造
                            output_path = output_dir / file_path.name
                        
                        # 患者IDのマッピングを記録
                        if hasattr(dcm, 'PatientID') and dcm.PatientID:
                            original_id = dcm.PatientID
                            if original_id not in self.patient_id_map:
                                # 新しいIDを生成
                                new_id = self.generate_anonymous_id(original_id)
                                
                                self.patient_id_map[original_id] = new_id
                                summary["患者ID対応表"][original_id] = new_id
                                
                                # 患者IDの一部をマスク処理して表示
                                masked_id = self._mask_patient_id(original_id)
                                self.log_message(f"患者ID対応: {masked_id} → {new_id}")
                        
                        # ファイルを匿名化して保存
                        self.log_message(f'処理中: {file_path.name} (タイプ: {file_type})')
                        
                        # DICOMファイルを匿名化
                        changes = self.anonymize_dicom(dcm, anonymization_profile, remove_private_tags)
                        
                        # 匿名化されたDICOMを保存
                        try:
                            # 警告メッセージを抑制するために、特定のタグの長さを確認して調整
                            for tag_name in ["StationName", "InstitutionName", "ReferringPhysicianName"]:
                                if hasattr(dcm, tag_name):
                                    value = getattr(dcm, tag_name)
                                    # SH (Short String) タイプのタグは16文字以内に制限
                                    if len(str(value)) > 16:
                                        setattr(dcm, tag_name, str(value)[:16])
                                        self.logger.warning(f"{tag_name}の値が長すぎるため切り詰めました: {value} -> {str(value)[:16]}")
                            
                            # UIタイプのタグを確認（MIMなどの無効な値を修正）
                            for elem in dcm:
                                if elem.VR == "UI" and elem.value and not str(elem.value).startswith("1.2."):
                                    # UIタイプは通常1.2.で始まるUID形式
                                    if str(elem.value) == "MIM":
                                        # MIMを有効なUIDに置き換え
                                        elem.value = generate_uid()
                                        self.logger.warning(f"無効なUI値を修正: {elem.tag} MIM -> {elem.value}")
                            
                            # 出力ディレクトリが存在することを確認
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 案B: 標準DICOMファイルメタ情報を強制付与
                            # (force=Trueで読んだ非標準ファイルも正しく保存される)
                            if not hasattr(dcm, 'file_meta') or dcm.file_meta is None:
                                dcm.file_meta = FileMetaDataset()
                            if not hasattr(dcm.file_meta, 'MediaStorageSOPClassUID') and hasattr(dcm, 'SOPClassUID'):
                                dcm.file_meta.MediaStorageSOPClassUID = dcm.SOPClassUID
                            if not hasattr(dcm.file_meta, 'MediaStorageSOPInstanceUID') and hasattr(dcm, 'SOPInstanceUID'):
                                dcm.file_meta.MediaStorageSOPInstanceUID = dcm.SOPInstanceUID
                            if not hasattr(dcm.file_meta, 'TransferSyntaxUID') or not dcm.file_meta.TransferSyntaxUID:
                                dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                            
                            # ファイルを保存（write_like_original=FalseでDICMヘッダーを付与）
                            dcm.save_as(str(output_path), write_like_original=False)
                            self.log_message(f"匿名化ファイル保存完了: {output_path.name}")
                        except Exception as save_error:
                            self.log_message(f"ファイル保存エラー: {str(save_error)}")
                            raise save_error
                        
                        summary["ファイル詳細"].append({
                            "ファイル名": file_path.name,
                            "タイプ": file_type,
                            "状態": "成功",
                            "変更フィールド": changes
                        })
                        summary["成功"] += 1
                        
                    except pydicom.errors.InvalidDicomError:
                        error_msg = f'DICOMファイルではないためスキップ: {file_path.name}'
                        self.log_message(error_msg)
                        summary["ファイル詳細"].append({
                            "ファイル名": file_path.name,
                            "タイプ": "非DICOM",
                            "状態": "スキップ"
                        })
                        summary["スキップ"] += 1
                        
                except Exception as e:
                    error_msg = f'処理エラー {file_path.name}: {str(e)}'
                    self.log_message(error_msg)
                    self.logger.error(traceback.format_exc())
                    summary["ファイル詳細"].append({
                        "ファイル名": file_path.name,
                        "タイプ": "エラー",
                        "状態": "失敗",
                        "エラー詳細": str(e)
                    })
                    summary["エラー"] += 1
            
            # 処理終了時間を記録
            summary["処理終了時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # JSON形式のサマリーファイルを作成
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.log_message("\n処理完了！")
            self.log_message(f"ログファイル: {log_path}")
            self.log_message(f"サマリーファイル: {summary_path}")
            
            if self.root and hasattr(self, 'status_var') and self.status_var:
                self.status_var.set(f"処理完了: 成功 {summary['成功']}, スキップ {summary['スキップ']}, エラー {summary['エラー']}")
            
            # ファイルハンドラーを削除
            self.logger.removeHandler(file_handler)
            
        except Exception as e:
            error_msg = f"予期せぬエラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            if self.root and hasattr(self, 'status_var') and self.status_var:
                self.status_var.set("エラーが発生しました")
    
    def _mask_patient_id(self, patient_id):
        """患者IDをマスク処理（表示用）"""
        id_str = str(patient_id)
        if len(id_str) > 4:
            return id_str[:2] + "***" + id_str[-2:]
        else:
            return "***"
