#!/usr/8/env python3
# -*- coding: utf-8 -*-

"""
DICOM Anonymization Checker

匿名化処理後のDICOMファイルが「本当に匿名化できているか」を検証するスタンドアロンツール。
2つのモードをサポート：
1. 単独スキャン (--scan): 匿名化済みディレクトリ内の個人情報残存をチェック
2. ペア比較 (--compare): 原本と匿名化済みファイルの差分を確認
"""

import os
import argparse
import json
import traceback
from pathlib import Path
from datetime import datetime

try:
    import pydicom
except ImportError:
    print("エラー: pydicom モジュールがインストールされていません。")
    print("インストール方法: pip install pydicom")
    exit(1)

# 出力先ディレクトリ
LOG_DIR = Path("DICOM_LOGS")

class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ValidationRules:
    """匿名化検証ルールを定義するクラス"""
    def __init__(self):
        # 必ず匿名化されるべきタグのリスト
        self.must_anonymize_tags = [
            "PatientName", "PatientID", "PatientBirthDate", "PatientAddress",
            "PatientTelephoneNumbers", "ReferringPhysicianName", "PhysiciansOfRecord",
            "PerformingPhysicianName", "InstitutionName", "InstitutionAddress",
            "StationName", "OperatorsName"
        ]
        
        # UIDタグのリスト
        self.uid_tags = [
            "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"
        ]
        
        # 日付関連のタグ
        self.date_tags = [
            "StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate"
        ]
        
        # RT特有のタグ
        self.rt_specific_tags = [
            "StructureSetLabel", "StructureSetName", "ROIName", "PlanLabel"
        ]

class AnonymizationChecker:
    def __init__(self):
        self.rules = ValidationRules()
        LOG_DIR.mkdir(exist_ok=True, parents=True)
    
    def _find_dicom_files(self, directory, exclude_dirs=None):
        """DICOMファイルを検索（指定ディレクトリを除外）"""
        if exclude_dirs is None:
            exclude_dirs = []
        
        dicom_files = []
        exclude_paths = [Path(d).absolute() for d in exclude_dirs]
        
        for root, _, files in os.walk(directory):
            root_path = Path(root).absolute()
            
            # 除外ディレクトリの下にあるかチェック
            is_excluded = False
            for excl in exclude_paths:
                if str(root_path).startswith(str(excl)):
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
                
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in ['.lnk', '.ini', '.txt', '.log', '.json', '.md']:
                    continue
                    
                # 簡易的なDICOMチェック
                try:
                    with open(file_path, 'rb') as f:
                        f.seek(128)
                        if f.read(4) == b"DICM":
                            dicom_files.append(file_path)
                        else:
                            # 拡張子なしでもDICOMかもしれないため、ヘッダがない場合はpydicomで少し読んでみる
                            try:
                                pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                                dicom_files.append(file_path)
                            except:
                                pass
                except:
                    pass
        return dicom_files

    def print_colored(self, text, color):
        print(f"{color}{text}{TerminalColors.ENDC}")

    def _check_tag_empty_or_anonymous(self, value):
        """値が空、もしくはANONYMOUSなどのダミー値になっているか"""
        val_str = str(value).strip().upper()
        if not val_str:
            return True
        if "ANONYMOUS" in val_str or "ANON" in val_str:
            return True
        if val_str == "19000101" or val_str == "20000101":
            return True
        # 000Y (年齢) や O (性別)
        if val_str in ["000Y", "O"]:
            return True
        return False

    def scan_directory(self, target_dir):
        """モードA: 単独スキャン"""
        target_dir = Path(target_dir)
        if not target_dir.exists():
            self.print_colored(f"エラー: ディレクトリが存在しません -> {target_dir}", TerminalColors.FAIL)
            return None

        self.print_colored(f"スキャン開始: {target_dir}", TerminalColors.OKCYAN)
        files = self._find_dicom_files(target_dir)
        self.print_colored(f"対象ファイル数: {len(files)}", TerminalColors.OKCYAN)
        
        results = {
            "mode": "scan",
            "target_dir": str(target_dir),
            "scanned_files": len(files),
            "warnings": [],
            "errors": [],
            "stats": {
                "private_tags_found": 0,
                "suspicious_must_tags": 0,
                "files_with_issues": set()
            },
            "file_details": []
        }
        
        for file_path in files:
            try:
                dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                file_issues = []
                
                # プライベートタグのチェック
                private_tags = [tag for tag in dcm.keys() if tag.is_private]
                if private_tags:
                    results["stats"]["private_tags_found"] += len(private_tags)
                    file_issues.append(f"プライベートタグが {len(private_tags)} 個残存")
                
                # 必須タグのチェック
                for tag in self.rules.must_anonymize_tags:
                    if hasattr(dcm, tag):
                        val = getattr(dcm, tag)
                        if not self._check_tag_empty_or_anonymous(val):
                            results["stats"]["suspicious_must_tags"] += 1
                            # PatientIDについてはハッシュ化されているかもしれないので、完全なエラーとしないが警告
                            if tag == "PatientID":
                                if not str(val).isdigit() or len(str(val)) < 5:
                                    file_issues.append(f"不完全な PatientID の疑い: {val}")
                            else:
                                file_issues.append(f"個人情報残存の疑い ({tag}): {val}")
                
                # 日付タグのチェック
                for tag in self.rules.date_tags:
                    if hasattr(dcm, tag):
                        val = getattr(dcm, tag)
                        if str(val) != "20000101" and str(val) != "":
                            file_issues.append(f"実日付残存の疑い ({tag}): {val}")

                # UIDのチェック (1.2.826.0.1.3680043.2.1125等、特定の既知ルートで始まっていればOKとする)
                # ここではpydicomの生成する root = 1.2.826.0.1.3680043.8.498 か確認
                for tag in self.rules.uid_tags:
                    if hasattr(dcm, tag):
                        val = str(getattr(dcm, tag))
                        if not val.startswith("1.2.826.0.1.3680043.8.498") and not val.startswith("2.25."):
                             file_issues.append(f"元UID残存の疑い ({tag}): {val}")

                detail = {"file": str(file_path.name), "issues": file_issues}
                results["file_details"].append(detail)
                
                if file_issues:
                    results["stats"]["files_with_issues"].add(str(file_path.name))
                    for issue in file_issues:
                        results["warnings"].append(f"{file_path.name}: {issue}")

            except Exception as e:
                results["errors"].append(f"{file_path.name} の読み込みエラー: {str(e)}")
        
        # Setをリストに戻す
        results["stats"]["files_with_issues"] = list(results["stats"]["files_with_issues"])
        return results

    def _generate_matching_key(self, dcm):
        key_parts = []
        if hasattr(dcm, 'Modality'): key_parts.append(f"MOD:{dcm.Modality}")
        if hasattr(dcm, 'SeriesNumber'): key_parts.append(f"SER:{dcm.SeriesNumber}")
        if hasattr(dcm, 'InstanceNumber'): key_parts.append(f"INS:{dcm.InstanceNumber}")
        if hasattr(dcm, 'SOPClassUID'): key_parts.append(f"SOP:{dcm.SOPClassUID}")
        
        # 固有の識別として ImagePositionPatient などがあれば使う
        if hasattr(dcm, 'ImagePositionPatient'):
            pos = [str(int(float(p))) for p in dcm.ImagePositionPatient]
            key_parts.append(f"POS:{','.join(pos)}")
            
        if len(key_parts) >= 2:
            return "|".join(key_parts)
        return None

    def compare_directories(self, original_dir, anonymized_dir):
        """モードB: ペア比較"""
        orig_dir = Path(original_dir)
        anon_dir = Path(anonymized_dir)
        
        if not orig_dir.exists() or not anon_dir.exists():
            self.print_colored("エラー: 指定されたディレクトリが存在しません。", TerminalColors.FAIL)
            return None
            
        self.print_colored(f"ペア比較開始:", TerminalColors.OKCYAN)
        self.print_colored(f"  原本: {orig_dir}", TerminalColors.OKCYAN)
        self.print_colored(f"  匿名化: {anon_dir}", TerminalColors.OKCYAN)
        
        orig_files = self._find_dicom_files(orig_dir, exclude_dirs=[anon_dir])
        anon_files = self._find_dicom_files(anon_dir)
        
        self.print_colored(f"原本ファイル数: {len(orig_files)}", TerminalColors.OKCYAN)
        self.print_colored(f"匿名化ファイル数: {len(anon_files)}", TerminalColors.OKCYAN)
        
        results = {
            "mode": "compare",
            "original_dir": str(orig_dir),
            "anonymized_dir": str(anon_dir),
            "original_files_count": len(orig_files),
            "anonymized_files_count": len(anon_files),
            "matched_files": 0,
            "stats": {
                "must_tags_changed": 0,
                "must_tags_unchanged": 0,
                "uids_changed": 0,
                "uids_unchanged": 0,
                "private_tags_removed": 0,
                "private_tags_remaining": 0
            },
            "warnings": [],
            "errors": [],
            "file_details": []
        }
        
        # マッチング辞書の作成
        orig_map = {}
        for f in orig_files:
            try:
                dcm = pydicom.dcmread(str(f), force=True, stop_before_pixels=True)
                key = self._generate_matching_key(dcm)
                if key:
                    orig_map[key] = f
            except:
                pass
                
        for anon_f in anon_files:
            try:
                anon_dcm = pydicom.dcmread(str(anon_f), force=True, stop_before_pixels=True)
                key = self._generate_matching_key(anon_dcm)
                orig_f = None
                
                # 同名ファイルで直接マッチを優先
                expected_orig = orig_dir / anon_f.name
                if expected_orig in orig_files:
                    orig_f = expected_orig
                elif key and key in orig_map:
                    orig_f = orig_map[key]
                
                if not orig_f:
                    results["warnings"].append(f"マッチする原本が見つかりません: {anon_f.name}")
                    continue
                    
                results["matched_files"] += 1
                orig_dcm = pydicom.dcmread(str(orig_f), force=True, stop_before_pixels=True)
                
                detail = {"file": anon_f.name, "diffs": []}
                
                # 必須タグの比較
                for tag in self.rules.must_anonymize_tags:
                    orig_val = getattr(orig_dcm, tag, "N/A") if hasattr(orig_dcm, tag) else "N/A"
                    anon_val = getattr(anon_dcm, tag, "N/A") if hasattr(anon_dcm, tag) else "N/A"
                    
                    if str(orig_val) != str(anon_val):
                        results["stats"]["must_tags_changed"] += 1
                    else:
                        if orig_val != "N/A" and str(orig_val).strip() != "":
                            results["stats"]["must_tags_unchanged"] += 1
                            detail["diffs"].append(f"必須タグ未変更 ({tag}): {orig_val}")
                            
                # UIDの比較
                for tag in self.rules.uid_tags:
                    orig_val = getattr(orig_dcm, tag, "N/A") if hasattr(orig_dcm, tag) else "N/A"
                    anon_val = getattr(anon_dcm, tag, "N/A") if hasattr(anon_dcm, tag) else "N/A"
                    if str(orig_val) != str(anon_val):
                        results["stats"]["uids_changed"] += 1
                    else:
                        if orig_val != "N/A":
                            results["stats"]["uids_unchanged"] += 1
                            detail["diffs"].append(f"UID未変更 ({tag}): {orig_val}")
                            
                # プライベートタグ
                orig_priv = [t for t in orig_dcm.keys() if t.is_private]
                anon_priv = [t for t in anon_dcm.keys() if t.is_private]
                
                if len(orig_priv) > 0 and len(anon_priv) == 0:
                    results["stats"]["private_tags_removed"] += 1
                elif len(anon_priv) > 0:
                    results["stats"]["private_tags_remaining"] += 1
                    detail["diffs"].append(f"プライベートタグ残存: {len(anon_priv)}個")
                
                if detail["diffs"]:
                    results["file_details"].append(detail)
                    
            except Exception as e:
                results["errors"].append(f"{anon_f.name} の処理エラー: {str(e)}")
                
        return results

    def generate_report(self, results):
        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"checker_scan_{timestamp}" if results["mode"] == "scan" else f"checker_compare_{timestamp}"
        
        # 1. Console Output
        self.print_colored("\n" + "="*40, TerminalColors.HEADER)
        self.print_colored(" 匿名化チェッカー レポート", TerminalColors.BOLD)
        self.print_colored("="*40, TerminalColors.HEADER)
        
        if results["mode"] == "scan":
            self.print_colored(f"モード: 単独スキャン", TerminalColors.OKCYAN)
            self.print_colored(f"スキャン対象: {results['target_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"ファイル数: {results['scanned_files']}", TerminalColors.OKCYAN)
            
            stats = results["stats"]
            issues_count = len(stats["files_with_issues"])
            
            if issues_count == 0 and not results["errors"]:
                self.print_colored("\n✅ すべてのファイルで個人情報は見つかりませんでした！", TerminalColors.OKGREEN)
            else:
                self.print_colored(f"\n⚠️ 問題が疑われるファイル数: {issues_count}", TerminalColors.WARNING)
                self.print_colored(f"  - 残存プライベートタグの総数: {stats['private_tags_found']}", TerminalColors.WARNING)
                self.print_colored(f"  - 疑わしい必須タグの総数: {stats['suspicious_must_tags']}", TerminalColors.WARNING)
                
        else:
            self.print_colored(f"モード: ペア比較", TerminalColors.OKCYAN)
            self.print_colored(f"原本: {results['original_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"匿名化: {results['anonymized_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"マッチファイル数: {results['matched_files']}/{results['anonymized_files_count']}", TerminalColors.OKCYAN)
            
            stats = results["stats"]
            self.print_colored("\n[変更統計]", TerminalColors.BOLD)
            self.print_colored(f"  必須タグ変更: {stats['must_tags_changed']} / 未変更: {stats['must_tags_unchanged']}", TerminalColors.OKBLUE)
            self.print_colored(f"  UIDタグ変更: {stats['uids_changed']} / 未変更: {stats['uids_unchanged']}", TerminalColors.OKBLUE)
            
            if stats["must_tags_unchanged"] == 0 and stats["uids_unchanged"] == 0 and stats["private_tags_remaining"] == 0:
                self.print_colored("\n✅ 比較検証に合格しました！", TerminalColors.OKGREEN)
            else:
                self.print_colored("\n⚠️ 匿名化が不十分な箇所があります。", TerminalColors.WARNING)

        if results["errors"]:
            self.print_colored("\n❌ エラーが発生しました:", TerminalColors.FAIL)
            for err in results["errors"][:5]:
                self.print_colored(f"  {err}", TerminalColors.FAIL)
            if len(results["errors"]) > 5:
                self.print_colored(f"  ...他 {len(results['errors']) - 5} 件", TerminalColors.FAIL)

        # 2. Markdown Report
        md_path = LOG_DIR / f"{prefix}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# DICOM Anonymization Checker Report\n\n")
            f.write(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Mode**: {results['mode']}\n")
            
            if results["mode"] == "scan":
                f.write(f"- **Target Directory**: `{results['target_dir']}`\n")
                f.write(f"- **Scanned Files**: {results['scanned_files']}\n\n")
                f.write("## Summary\n")
                
                stats = results["stats"]
                if len(stats["files_with_issues"]) == 0:
                    f.write("✅ **No personal information found in any files.**\n\n")
                else:
                    f.write("⚠️ **Potential issues detected!**\n\n")
                    f.write(f"- Files with issues: {len(stats['files_with_issues'])}\n")
                    f.write(f"- Private tags found: {stats['private_tags_found']}\n")
                    f.write(f"- Suspicious must-anonymize tags: {stats['suspicious_must_tags']}\n\n")
                    
                    f.write("## Details\n")
                    for warn in results["warnings"][:20]:
                        f.write(f"- {warn}\n")
                    if len(results["warnings"]) > 20:
                         f.write(f"- ...and {len(results['warnings']) - 20} more warnings.\n")
            else:
                f.write(f"- **Original Directory**: `{results['original_dir']}`\n")
                f.write(f"- **Anonymized Directory**: `{results['anonymized_dir']}`\n")
                f.write(f"- **Matched Files**: {results['matched_files']}\n\n")
                
                stats = results["stats"]
                f.write("## Statistics\n")
                f.write(f"- Must-anonymize tags changed: {stats['must_tags_changed']}\n")
                f.write(f"- Must-anonymize tags unchanged: {stats['must_tags_unchanged']}\n")
                f.write(f"- UID tags changed: {stats['uids_changed']}\n")
                f.write(f"- UID tags unchanged: {stats['uids_unchanged']}\n")
                f.write(f"- Private tags removed (files): {stats['private_tags_removed']}\n")
                f.write(f"- Private tags remaining (files): {stats['private_tags_remaining']}\n\n")
                
                if stats["must_tags_unchanged"] > 0 or stats["uids_unchanged"] > 0:
                    f.write("⚠️ **Warning: Some tags were not changed!**\n\n")
                    f.write("## Details\n")
                    for d in results["file_details"][:20]:
                        f.write(f"### {d['file']}\n")
                        for diff in d["diffs"]:
                            f.write(f"- {diff}\n")
                    if len(results["file_details"]) > 20:
                        f.write(f"\n...and {len(results['file_details']) - 20} more files with issues.\n")
            
            if results["errors"]:
                f.write("\n## Errors\n")
                for err in results["errors"]:
                    f.write(f"- `{err}`\n")

        # 3. Text Report (Simple copy of Markdown for ease of use)
        txt_path = LOG_DIR / f"{prefix}.txt"
        import shutil
        shutil.copy(md_path, txt_path)

        # 4. JSON Report (Full details)
        json_path = LOG_DIR / f"{prefix}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            # Set is already converted to list
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.print_colored(f"\nレポートを出力しました:", TerminalColors.OKGREEN)
        self.print_colored(f"  - Markdown: {md_path}", TerminalColors.OKGREEN)
        self.print_colored(f"  - Text: {txt_path}", TerminalColors.OKGREEN)
        self.print_colored(f"  - JSON: {json_path}", TerminalColors.OKGREEN)

def main():
    parser = argparse.ArgumentParser(description="DICOM Anonymization Checker")
    parser.add_argument("--scan", type=str, metavar="DIR", help="匿名化済みディレクトリ内の個人情報残存をスキャンします")
    parser.add_argument("--compare", nargs=2, metavar=("ORIG_DIR", "ANON_DIR"), help="原本と匿名化済みファイルの差分を比較します")
    
    args = parser.parse_args()
    checker = AnonymizationChecker()
    
    if args.scan:
        res = checker.scan_directory(args.scan)
        checker.generate_report(res)
    elif args.compare:
        res = checker.compare_directories(args.compare[0], args.compare[1])
        checker.generate_report(res)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
