"""
ファイル操作に関連するユーティリティ関数を提供するモジュール
"""

import os
import pydicom
import numpy as np
from pathlib import Path

def find_dicom_files(directory):
    """
    ディレクトリ内のDICOMファイルを再帰的に検索
    
    Args:
        directory: 検索するディレクトリのパス
        
    Returns:
        DICOMファイルのパスのリスト
    """
    dicom_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            
            # 非DICOM拡張子をスキップ
            if file_path.suffix.lower() in ['.lnk', '.ini', '.txt', '.log']:
                continue
                
            try:
                # DICOMファイルとして読み込めるか確認
                dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                
                # DICOMファイルの判定条件を緩和
                # SOPClassUIDがなくても、他の一般的なDICOMタグがあればDICOMファイルとみなす
                is_dicom = False
                
                # SOPClassUIDがあればDICOMファイル
                if hasattr(dcm, 'SOPClassUID'):
                    is_dicom = True
                # モダリティがあればDICOMファイル
                elif hasattr(dcm, 'Modality'):
                    is_dicom = True
                # 患者IDがあればDICOMファイル
                elif hasattr(dcm, 'PatientID'):
                    is_dicom = True
                # 少なくとも5つ以上のDICOMタグがあればDICOMファイルとみなす
                elif len(dcm) >= 5:
                    is_dicom = True
                
                if is_dicom:
                    dicom_files.append(file_path)
            except Exception as e:
                # エラーの詳細をログに出力（デバッグ用）
                # print(f"ファイル読み込みエラー: {file_path} - {e}")
                pass
    
    return dicom_files

def get_relative_path(file_path, base_dir):
    """
    ベースディレクトリからの相対パスを取得
    
    Args:
        file_path: ファイルの絶対パス
        base_dir: ベースディレクトリ
        
    Returns:
        ベースディレクトリからの相対パス
    """
    file_path = Path(file_path)
    base_dir = Path(base_dir)
    
    try:
        return file_path.relative_to(base_dir)
    except ValueError:
        return file_path.name

def ensure_directory_exists(directory_path):
    """
    ディレクトリが存在するかを確認し、存在しなければ作成
    
    Args:
        directory_path: 作成するディレクトリのパス
        
    Returns:
        作成されたディレクトリのPathオブジェクト
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def copy_directory_structure(src_dir, dst_dir):
    """
    ソースディレクトリの構造をコピー（ファイルはコピーしない）
    
    Args:
        src_dir: コピー元ディレクトリ
        dst_dir: コピー先ディレクトリ
        
    Returns:
        作成されたディレクトリの数
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    
    # コピー先ディレクトリを作成
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    # サブディレクトリを再帰的に作成
    created_dirs = 0
    for root, dirs, _ in os.walk(src_dir):
        for dir_name in dirs:
            src_subdir = Path(root) / dir_name
            rel_path = get_relative_path(src_subdir, src_dir)
            dst_subdir = dst_dir / rel_path
            
            dst_subdir.mkdir(exist_ok=True)
            created_dirs += 1
    
    return created_dirs

def compare_directory_structure(original_dir, anonymized_dir, log_func=print):
    """
    2つのディレクトリの構造を比較し、詳細なレポートを生成
    
    Args:
        original_dir: 原本ディレクトリ
        anonymized_dir: 匿名化ディレクトリ
        log_func: ログ出力関数
        
    Returns:
        比較結果を含む辞書
    """
    original_dir = Path(original_dir)
    anonymized_dir = Path(anonymized_dir)
    
    if not original_dir.exists() or not anonymized_dir.exists():
        log_func("指定されたディレクトリが存在しません。")
        return {"summary": ["指定されたディレクトリが存在しません。"]}
    
    # ファイル数をカウント
    original_files = find_dicom_files(original_dir)
    anonymized_files = find_dicom_files(anonymized_dir)
    
    log_func(f"原本ディレクトリのDICOMファイル数: {len(original_files)}")
    log_func(f"匿名化ディレクトリのDICOMファイル数: {len(anonymized_files)}")
    
    # 結果を格納
    summary = []
    summary.append("=== ディレクトリ比較結果 ===")
    summary.append(f"原本ディレクトリ: {original_dir}")
    summary.append(f"匿名化ディレクトリ: {anonymized_dir}")
    summary.append(f"原本DICOMファイル数: {len(original_files)}")
    summary.append(f"匿名化DICOMファイル数: {len(anonymized_files)}")
    
    if len(original_files) == len(anonymized_files):
        summary.append("\n✅ ファイル数一致: 原本と匿名化ファイルの数が一致しています。")
    else:
        summary.append("\n⚠️ ファイル数不一致: 原本と匿名化ファイルの数が一致していません。")
        if len(original_files) > len(anonymized_files):
            summary.append(f"  不足ファイル数: {len(original_files) - len(anonymized_files)}")
        else:
            summary.append(f"  過剰ファイル数: {len(anonymized_files) - len(original_files)}")
    
    # モダリティの分布を取得
    original_modalities = {}
    anonymized_modalities = {}
    
    for file_path in original_files:
        try:
            dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
            if hasattr(dcm, 'Modality'):
                modality = dcm.Modality
                if modality in original_modalities:
                    original_modalities[modality] += 1
                else:
                    original_modalities[modality] = 1
        except:
            pass
    
    for file_path in anonymized_files:
        try:
            dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
            if hasattr(dcm, 'Modality'):
                modality = dcm.Modality
                if modality in anonymized_modalities:
                    anonymized_modalities[modality] += 1
                else:
                    anonymized_modalities[modality] = 1
        except:
            pass
    
    # モダリティ分布をサマリーに追加
    summary.append("\n=== モダリティ分布 ===")
    modalities = list(set(list(original_modalities.keys()) + list(anonymized_modalities.keys())))
    original_counts = [original_modalities.get(m, 0) for m in modalities]
    anonymized_counts = [anonymized_modalities.get(m, 0) for m in modalities]
    
    for modality in modalities:
        orig_count = original_modalities.get(modality, 0)
        anon_count = anonymized_modalities.get(modality, 0)
        status = "✅" if orig_count == anon_count else "⚠️"
        summary.append(f"{status} {modality}: 原本 {orig_count}, 匿名化 {anon_count}")
    
    return {
        "summary": summary,
        "original_files": len(original_files),
        "anonymized_files": len(anonymized_files),
        "modality_data": {
            "modalities": modalities,
            "original_counts": original_counts,
            "anonymized_counts": anonymized_counts
        }
    }
