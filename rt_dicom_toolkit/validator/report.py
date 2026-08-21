"""
Validation report generation.
"""

from datetime import datetime
from pathlib import Path

def generate_summary_report(summary, rules):
    """
    Generate a text summary from validation results.
    
    Args:
        summary: Aggregated validation results.
        rules: Active ValidationRules instance.
        
    Returns:
        Generated report text.
    """
    report = []
    
    report.append("=== Anonymization Validation Summary ===")
    report.append(f"Validation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total files: {summary['total_files']}")
    report.append(f"Matched files: {summary['matched_files']}")
    report.append("")
    
    # Overall anonymization status.
    total_must_tags = len(rules.must_anonymize_tags) * summary['matched_files']
    total_anonymized = sum(summary['must_anonymize_stats'][tag]['anonymized'] for tag in rules.must_anonymize_tags)
    
    if total_must_tags > 0:
        anonymization_rate = total_anonymized / total_must_tags * 100
        report.append(f"Required-attribute anonymization rate: {anonymization_rate:.1f}%")
        
        if anonymization_rate >= 95:
            report.append("✅ Anonymization status: good (at least 95% processed correctly)")
        elif anonymization_rate >= 80:
            report.append("⚠️ Anonymization status: review required (80% to less than 95%)")
        else:
            report.append("❌ Anonymization status: insufficient (less than 80%)")
    
    report.append("")
    report.append("--- Required anonymization attributes ---")
    for tag in rules.must_anonymize_tags:
        anonymized = summary['must_anonymize_stats'][tag]['anonymized']
        not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
        total = anonymized + not_anonymized
        
        if total > 0:
            rate = anonymized / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {anonymized}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- UID changes ---")
    for tag in rules.uid_tags:
        changed = summary['uid_stats'][tag]['changed']
        not_changed = summary['uid_stats'][tag]['not_changed']
        total = changed + not_changed
        
        if total > 0:
            rate = changed / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {changed}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- Structure preservation ---")
    for tag in rules.structure_tags:
        preserved = summary['structure_stats'][tag]['preserved']
        not_preserved = summary['structure_stats'][tag]['not_preserved']
        total = preserved + not_preserved
        
        if total > 0:
            rate = preserved / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {preserved}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- Private-tag removal ---")
    removed = summary['private_tags_stats']['removed']
    not_removed = summary['private_tags_stats']['not_removed']
    total = removed + not_removed
    
    if total > 0:
        rate = removed / total * 100
        status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
        report.append(f"{status} Private tags removed: {removed}/{total} ({rate:.1f}%)")
    
    # Modality distribution.
    report.append("")
    report.append("--- Modality distribution ---")
    for modality, count in summary['modality_stats'].items():
        report.append(f"{modality}: {count} files")
    
    # Patient-ID mapping.
    if summary['patient_id_map']:
        report.append("")
        report.append("--- Patient ID mapping (up to 10 entries) ---")
        count = 0
        for orig_id, anon_id in summary['patient_id_map'].items():
            # Mask part of the original patient ID.
            if len(orig_id) > 4:
                masked_id = orig_id[:2] + "***" + orig_id[-2:]
            else:
                masked_id = "***"
                
            report.append(f"{masked_id} -> {anon_id}")
            count += 1
            if count >= 10:
                report.append(f"...and {len(summary['patient_id_map']) - 10} more")
                break
    
    return "\n".join(report)

def generate_validation_report_filename(prefix="validation_summary"):
    """
    Generate a timestamped validation-report file name.
    
    Args:
        prefix: File-name prefix.
        
    Returns:
        Timestamped file name.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.txt"

def save_report(report_text, report_dir, filename=None):
    """
    Save a validation report.
    
    Args:
        report_text: Report contents.
        report_dir: Destination directory.
        filename: Optional file name.
        
    Returns:
        Path to the saved report.
    """
    if filename is None:
        filename = generate_validation_report_filename()
    
    report_path = Path(report_dir) / filename
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_path
