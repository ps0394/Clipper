#!/usr/bin/env python3
"""
Clipper Interactive Demo Runner

Provides guided demonstration of Clipper's standards-based evaluation capabilities.
Perfect for live demos, training sessions, and immediate validation.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any


class ClipperDemo:
    """Interactive Clipper demonstration orchestrator."""
    
    def __init__(self):
        self.demo_dir = Path("clipper-demo-live")
        self.urls_file = "clipper-demo-urls.txt"
        
    def print_banner(self, text: str, char: str = "="):
        """Print formatted banner."""
        print(f"\n{char * 60}")
        print(f"  {text}")
        print(f"{char * 60}\n")
        
    def print_step(self, step: str, description: str):
        """Print demo step with formatting."""
        print(f"\n🚀 {step}")
        print(f"   {description}")
        print("-" * 50)
        
    def wait_for_user(self, prompt: str = "Press Enter to continue..."):
        """Wait for user input to proceed."""
        input(f"\n💡 {prompt}")
        
    def run_clipper_evaluation(self) -> bool:
        """Run Clipper evaluation and return success status."""
        try:
            print("⏳ Running Clipper standards-based evaluation...")
            
            # Check if we're in the right directory and have the right Python
            python_cmd = sys.executable
            clipper_cmd = [
                python_cmd, "main.py", "express", 
                self.urls_file, 
                "--out", str(self.demo_dir),
                "--name", "demo",
                "--quiet"
            ]
            
            result = subprocess.run(clipper_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("[PASS] Clipper evaluation completed successfully!")
                return True
            else:
                print(f"❌ Evaluation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Evaluation timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"💥 Evaluation error: {e}")
            return False
    
    def show_results_summary(self):
        """Display evaluation results summary."""
        try:
            scores_file = self.demo_dir / "demo_scores.json"
            if not scores_file.exists():
                print("❌ Results file not found")
                return
                
            with open(scores_file) as f:
                results = json.load(f)
            
            print("\n[RESULTS] Clipper Evaluation Results:")
            print(f"├─ Total URLs Evaluated: {len(results)}")
            
            # Calculate summary stats
            scores = [r['parseability_score'] for r in results]
            avg_score = sum(scores) / len(scores)
            agent_ready = sum(1 for r in results if r['failure_mode'] in ['clean', 'minor_issues'])
            
            print(f"├─ Average Score: {avg_score:.1f}/100")
            print(f"└─ Agent-Ready: {agent_ready}/{len(results)} ({agent_ready/len(results)*100:.1f}%)")
            
            print(f"\n📋 Individual Results:")
            for i, result in enumerate(results[:5]):  # Show first 5
                score = result['parseability_score']
                mode = result['failure_mode']
                url = result.get('url', 'Unknown URL')
                emoji = '✅' if mode == 'clean' else '⚠️' if score >= 60 else '❌'
                print(f"  {emoji} {score:3.0f}/100 - {url}")
                
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more URLs")
                
        except Exception as e:
            print(f"💥 Error displaying results: {e}")
    
    def show_component_breakdown(self):
        """Show detailed component score breakdown."""
        try:
            scores_file = self.demo_dir / "demo_scores.json"
            with open(scores_file) as f:
                results = json.load(f)
            
            print("\n🎯 Standards-Based Component Analysis:")
            print("=" * 70)
            
            # Show first result as example
            if results:
                example = results[0]
                components = example.get('component_scores', {})
                
                print(f"📍 Sample Analysis: {example.get('url', 'Unknown')}")
                print(f"   Final Score: {example['parseability_score']:.1f}/100")
                print(f"   Classification: {example['failure_mode']}")
                print()
                
                # Component breakdown
                component_names = {
                    'wcag_accessibility': '🛡️ WCAG 2.1 Accessibility',
                    'semantic_html': '🏗️ W3C Semantic HTML', 
                    'structured_data': '📊 Schema.org Data',
                    'http_compliance': '🌐 HTTP Compliance',
                    'content_quality': '📝 Content Quality'
                }
                
                for comp_key, score in components.items():
                    name = component_names.get(comp_key, comp_key)
                    print(f"  {name}: {score:.1f}/100")
                
        except Exception as e:
            print(f"💥 Error showing component breakdown: {e}")
    
    def show_audit_trail(self):
        """Display audit trail information."""
        try:
            scores_file = self.demo_dir / "demo_scores.json"
            with open(scores_file) as f:
                results = json.load(f)
            
            if results:
                example = results[0]
                
                print("\n📋 Enterprise Audit Trail Sample:")
                print("=" * 50)
                
                # Standards authority
                authority = example.get('standards_authority', {})
                print("🏛️ Standards Authority Mapping:")
                for standard, auth in authority.items():
                    print(f"   • {standard}: {auth}")
                
                print(f"\n📊 Evaluation Methodology: {example.get('evaluation_methodology', 'Unknown')}")
                
                # Sample audit trail
                audit_trail = example.get('audit_trail', {})
                if audit_trail:
                    print("\n🔍 Sample Component Audit:")
                    for component, details in list(audit_trail.items())[:2]:  # Show first 2
                        print(f"   • {component}: {details.get('method', 'No details')}")
                
        except Exception as e:
            print(f"💥 Error showing audit trail: {e}")
    
    def run_demo(self):
        """Run complete Clipper demonstration."""
        
        self.print_banner("Clipper Live Demo", "🚀")
        
        print("Welcome to the Clipper Standards-Based Access Gate Demo!")
        print("\nClipper Key Features:")
        print("✅ API-Free Operation - No external dependencies")  
        print("✅ Standards-Based Scoring - WCAG 2.1, W3C, Schema.org, RFC 7231")
        print("✅ Enterprise Defensible - Complete audit trails")
        print("✅ Immediate Usability - Works from any command line")
        
        self.wait_for_user("Ready to start the demo?")
        
        # Step 1: Show demo URLs
        self.print_step("STEP 1", "Demo URL Collection")
        print("We'll evaluate a diverse set of documentation sites:")
        print("• Microsoft Learn (expected: high standards compliance)")
        print("• Developer Documentation (mixed results)")  
        print("• W3C/Schema.org (perfect semantic markup)")
        print("• Technical References (structured data examples)")
        
        try:
            with open(self.urls_file) as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"\n📊 Total URLs for evaluation: {len(urls)}")
        except FileNotFoundError:
            print(f"❌ Demo URLs file not found: {self.urls_file}")
            return
            
        self.wait_for_user("Ready to run Clipper evaluation?")
        
        # Step 2: Run evaluation  
        self.print_step("STEP 2", "Clipper Standards-Based Evaluation")
        success = self.run_clipper_evaluation()
        
        if not success:
            print("💥 Demo evaluation failed. Please check your setup.")
            return
            
        self.wait_for_user("Ready to analyze the results?")
        
        # Step 3: Show results
        self.print_step("STEP 3", "Results Analysis") 
        self.show_results_summary()
        
        self.wait_for_user("Ready to see component breakdown?")
        
        # Step 4: Component analysis
        self.print_step("STEP 4", "Standards Component Analysis")
        self.show_component_breakdown()
        
        self.wait_for_user("Ready to examine audit trails?")
        
        # Step 5: Audit trails
        self.print_step("STEP 5", "Enterprise Audit Trail")
        self.show_audit_trail()
        
        # Conclusion
        self.print_banner("Demo Complete! 🎉")
        print("Clipper Demonstrated:")
        print("✅ API-free evaluation of real documentation sites")
        print("✅ Standards-based scoring with complete traceability") 
        print("✅ Enterprise audit trails for compliance documentation")
        print("✅ Component-level insights for targeted improvements")
        
        print(f"\n📁 Full results available in: {self.demo_dir}/")
        print("🚀 Try Clipper on your own content - no setup required!")


def main():
    """Run Clipper interactive demo."""
    demo = ClipperDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo error: {e}")
        print("Please check your Clipper installation and try again.")


if __name__ == "__main__":
    main()