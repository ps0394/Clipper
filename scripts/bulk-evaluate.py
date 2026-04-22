#!/usr/bin/env python3
"""
Large-scale Clipper evaluation with progress tracking and summary reporting
Usage: python bulk-evaluate.py large-urls.txt --batch-size 50 --out bulk-results/
"""

import argparse
import json
import time
from pathlib import Path
import subprocess
import sys

def chunk_urls(url_file, batch_size):
    """Split large URL file into smaller batches"""
    with open(url_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    for i in range(0, len(urls), batch_size):
        yield urls[i:i + batch_size]

def run_bulk_evaluation(url_file, output_dir, batch_size=50):
    """Process URLs in batches with progress reporting"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    all_results = []
    batch_num = 0
    
    total_urls = sum(1 for line in open(url_file) if line.strip() and not line.startswith('#'))
    processed_urls = 0
    
    print(f"🔄 Processing {total_urls} URLs in batches of {batch_size}")
    start_time = time.time()
    
    for url_batch in chunk_urls(url_file, batch_size):
        batch_num += 1
        batch_file = output_path / f"batch_{batch_num}.txt"
        
        # Write batch URLs to temp file
        with open(batch_file, 'w') as f:
            for url in url_batch:
                f.write(f"{url}\n")
        
        # Run Clipper on batch  
        batch_output = output_path / f"batch_{batch_num}_results"
        cmd = [
            sys.executable, "-m", "retrievability.cli", "express", 
            str(batch_file), "--out", str(batch_output), "--quiet"
        ]
        
        print(f"📊 Processing batch {batch_num} ({len(url_batch)} URLs)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Load batch results
            with open(batch_output / "report_scores.json") as f:
                batch_scores = json.load(f)
                all_results.extend(batch_scores)
        else:
            print(f"❌ Batch {batch_num} failed: {result.stderr}")
        
        processed_urls += len(url_batch)
        elapsed = time.time() - start_time
        rate = processed_urls / elapsed
        eta = (total_urls - processed_urls) / rate if rate > 0 else 0
        
        print(f"   Progress: {processed_urls}/{total_urls} URLs ({processed_urls/total_urls*100:.1f}%)")
        print(f"   Rate: {rate:.1f} URLs/sec, ETA: {eta/60:.1f} minutes")
        
        # Cleanup batch file
        batch_file.unlink()
    
    # Generate summary report
    generate_bulk_summary(all_results, output_path, total_urls, elapsed)

def generate_bulk_summary(all_results, output_path, total_urls, elapsed):
    """Generate executive summary for large dataset"""
    
    if not all_results:
        print("❌ No results to summarize")
        return
        
    scores = [r['parseability_score'] for r in all_results]
    failure_modes = [r['failure_mode'] for r in all_results]
    
    # Calculate statistics
    avg_score = sum(scores) / len(scores)
    clean_count = failure_modes.count('clean')
    structure_missing = failure_modes.count('structure-missing') 
    extraction_noisy = failure_modes.count('extraction-noisy')
    
    # Score distribution
    high_scorers = len([s for s in scores if s >= 80])
    medium_scorers = len([s for s in scores if 60 <= s < 80])
    low_scorers = len([s for s in scores if s < 60])
    
    summary = {
        "evaluation_stats": {
            "total_urls_requested": total_urls,
            "total_urls_processed": len(all_results),
            "processing_time_minutes": elapsed / 60,
            "average_score": avg_score,
            "success_rate": len(all_results) / total_urls * 100
        },
        "score_distribution": {
            "agent_ready_80plus": {"count": high_scorers, "percentage": high_scorers/len(scores)*100},
            "needs_work_60_79": {"count": medium_scorers, "percentage": medium_scorers/len(scores)*100}, 
            "major_issues_below_60": {"count": low_scorers, "percentage": low_scorers/len(scores)*100}
        },
        "failure_modes": {
            "clean": {"count": clean_count, "percentage": clean_count/len(scores)*100},
            "structure_missing": {"count": structure_missing, "percentage": structure_missing/len(scores)*100},
            "extraction_noisy": {"count": extraction_noisy, "percentage": extraction_noisy/len(scores)*100}
        }
    }
    
    # Save summary
    with open(output_path / "bulk_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print executive summary 
    print(f"\n🎯 **BULK EVALUATION COMPLETE**")
    print(f"📊 Processed: {len(all_results)}/{total_urls} URLs in {elapsed/60:.1f} minutes")
    print(f"📈 Average Score: {avg_score:.1f}/100")
    print(f"✅ Agent-Ready (80+): {high_scorers} ({high_scorers/len(scores)*100:.1f}%)")
    print(f"⚠️  Needs Work (60-79): {medium_scorers} ({medium_scorers/len(scores)*100:.1f}%)")
    print(f"❌ Major Issues (<60): {low_scorers} ({low_scorers/len(scores)*100:.1f}%)")
    print(f"\n📄 Full summary: {output_path}/bulk_summary.json")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Large-scale Clipper evaluation')
    parser.add_argument('url_file', help='File containing URLs to evaluate')
    parser.add_argument('--out', default='bulk-evaluation', help='Output directory')
    parser.add_argument('--batch-size', type=int, default=50, help='URLs per batch')
    
    args = parser.parse_args()
    run_bulk_evaluation(args.url_file, args.out, args.batch_size)