#!/usr/bin/env python3
"""
GitHub Agent for URL Evaluation
Simple agent interface that triggers URL evaluation workflows and returns results.

Usage:
    python url-agent.py "https://docs.microsoft.com/en-us/azure/" "https://github.com/docs"
    python url-agent.py --file urls.txt
"""

import subprocess
import json
import time
import sys
import argparse
from pathlib import Path

class URLAgent:
    def __init__(self, repo="ps0394/Retrieval"):
        self.repo = repo
        self.workflow = "quick-evaluate.yml"
    
    def evaluate_urls(self, urls, name="agent-evaluation"):
        """Trigger workflow with URLs and return results"""
        print(f"🤖 Agent evaluating {len(urls)} URLs...")
        
        # Format URLs for workflow input
        urls_text = "\n".join(urls)
        
        # Trigger workflow via GitHub CLI
        print("🚀 Triggering evaluation workflow...")
        try:
            result = subprocess.run([
                "gh", "workflow", "run", self.workflow,
                "--repo", self.repo,
                "-f", f"urls={urls_text}",
                "-f", f"output_name={name}"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Workflow triggered successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to trigger workflow: {e.stderr}")
            return None
        
        # Wait for workflow to complete and get results
        return self._wait_for_results(name)
    
    def _wait_for_results(self, name, max_wait=300):
        """Wait for workflow to complete and fetch results"""
        print("⏳ Waiting for evaluation to complete...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Check for recent workflow runs
            try:
                result = subprocess.run([
                    "gh", "run", "list",
                    "--repo", self.repo,
                    "--workflow", self.workflow,
                    "--limit", "1",
                    "--json", "status,conclusion,number,url"
                ], capture_output=True, text=True, check=True)
                
                runs = json.loads(result.stdout)
                if runs and runs[0]["status"] == "completed":
                    if runs[0]["conclusion"] == "success":
                        print("✅ Evaluation completed successfully!")
                        return self._fetch_results(runs[0]["number"])
                    else:
                        print(f"❌ Evaluation failed: {runs[0]['conclusion']}")
                        print(f"🔗 Check details: {runs[0]['url']}")
                        return None
                        
            except subprocess.CalledProcessError:
                pass
            
            print("⏳ Still running... waiting 10 seconds")
            time.sleep(10)
        
        print("⏰ Timeout waiting for results")
        return None
    
    def _fetch_results(self, run_number):
        """Fetch results from completed workflow run"""
        try:
            # Download artifacts
            print("📥 Downloading results...")
            
            # List artifacts for the run
            result = subprocess.run([
                "gh", "run", "download", str(run_number),
                "--repo", self.repo,
                "--dir", "temp-results"
            ], capture_output=True, text=True, check=True)
            
            # Read the summary file
            results_dir = Path("temp-results")
            summary_files = list(results_dir.glob("**/summary.md"))
            
            if summary_files:
                with open(summary_files[0], 'r') as f:
                    summary = f.read()
                
                # Clean up
                import shutil
                shutil.rmtree(results_dir)
                
                return {
                    "summary": summary,
                    "run_number": run_number,
                    "status": "success"
                }
            else:
                print("📄 No summary file found in artifacts")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"📥 Failed to download results: {e.stderr}")
            return None

def main():
    parser = argparse.ArgumentParser(description="GitHub Agent for URL Evaluation")
    parser.add_argument("urls", nargs="*", help="URLs to evaluate")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--name", "-n", default="agent-eval", help="Evaluation name")
    
    args = parser.parse_args()
    
    # Collect URLs
    urls = []
    if args.file:
        with open(args.file, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip()])
    
    urls.extend(args.urls)
    
    if not urls:
        print("❌ No URLs provided. Use: python url-agent.py URL1 URL2 or --file urls.txt")
        return 1
    
    # Initialize agent
    agent = URLAgent()
    
    # Evaluate URLs
    results = agent.evaluate_urls(urls, args.name)
    
    if results:
        print("\n" + "="*50)
        print("📊 EVALUATION RESULTS")
        print("="*50)
        print(results["summary"])
        print(f"\n🔗 Full details: https://github.com/{agent.repo}/actions/runs/{results['run_number']}")
        return 0
    else:
        print("❌ Failed to get results")
        return 1

if __name__ == "__main__":
    exit(main())