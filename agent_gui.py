#!/usr/bin/env python3
"""
CompliSense AI Agent - macOS GUI Entry Point
File: agent_gui.py

This provides a native macOS experience for selecting input/output paths
and running compliance scans.
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import json
from datetime import datetime

# Add agent to path
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))

from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf


class CompliSenseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CompliSense AI - EU AI Act Compliance Scanner")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.scan_running = False

        # Set default output path to Documents/CompliSense
        default_output = Path.home() / "Documents" / "CompliSense"
        self.output_path.set(str(default_output))

        self.create_widgets()

    def create_widgets(self):
        """Create the main GUI layout"""

        # Header
        header_frame = tk.Frame(self.root, bg="#667eea", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🤖 CompliSense AI",
            font=("Helvetica", 24, "bold"),
            bg="#667eea",
            fg="white"
        )
        title_label.pack(pady=15)

        subtitle_label = tk.Label(
            header_frame,
            text="EU AI Act Compliance Scanner",
            font=("Helvetica", 12),
            bg="#667eea",
            fg="white"
        )
        subtitle_label.pack()

        # Main content frame
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = tk.Label(
            content_frame,
            text="Welcome! Let's scan your AI/ML project for EU AI Act compliance.",
            font=("Helvetica", 12),
            wraplength=700,
            justify=tk.LEFT
        )
        instructions.pack(anchor=tk.W, pady=(0, 20))

        # Input Path Section
        input_frame = tk.LabelFrame(
            content_frame,
            text="Step 1: Select Your ML Project",
            font=("Helvetica", 11, "bold"),
            padx=15,
            pady=15
        )
        input_frame.pack(fill=tk.X, pady=(0, 15))

        input_info = tk.Label(
            input_frame,
            text="Choose the root directory of your ML project (containing models, datasets, configs, etc.)",
            font=("Helvetica", 9),
            fg="#666",
            wraplength=650,
            justify=tk.LEFT
        )
        input_info.pack(anchor=tk.W, pady=(0, 10))

        input_path_frame = tk.Frame(input_frame)
        input_path_frame.pack(fill=tk.X)

        input_entry = tk.Entry(
            input_path_frame,
            textvariable=self.input_path,
            font=("Helvetica", 10),
            width=60
        )
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        input_button = tk.Button(
            input_path_frame,
            text="Browse...",
            command=self.browse_input,
            bg="#667eea",
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=5
        )
        input_button.pack(side=tk.LEFT)

        # Output Path Section
        output_frame = tk.LabelFrame(
            content_frame,
            text="Step 2: Choose Output Location",
            font=("Helvetica", 11, "bold"),
            padx=15,
            pady=15
        )
        output_frame.pack(fill=tk.X, pady=(0, 15))

        output_info = tk.Label(
            output_frame,
            text="Select where to save compliance reports, logs, and scan results",
            font=("Helvetica", 9),
            fg="#666",
            wraplength=650,
            justify=tk.LEFT
        )
        output_info.pack(anchor=tk.W, pady=(0, 10))

        output_path_frame = tk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X)

        output_entry = tk.Entry(
            output_path_frame,
            textvariable=self.output_path,
            font=("Helvetica", 10),
            width=60
        )
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        output_button = tk.Button(
            output_path_frame,
            text="Browse...",
            command=self.browse_output,
            bg="#667eea",
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=5
        )
        output_button.pack(side=tk.LEFT)

        # Scan Button
        self.scan_button = tk.Button(
            content_frame,
            text="🔍 Start Compliance Scan",
            command=self.start_scan,
            bg="#10b981",
            fg="white",
            font=("Helvetica", 14, "bold"),
            padx=30,
            pady=15,
            cursor="hand2"
        )
        self.scan_button.pack(pady=20)

        # Progress Section
        progress_frame = tk.LabelFrame(
            content_frame,
            text="Scan Progress",
            font=("Helvetica", 11, "bold"),
            padx=15,
            pady=15
        )
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=700
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Log output
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=12,
            font=("Courier", 9),
            bg="#f8f9fa",
            fg="#333"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready to scan",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Helvetica", 9),
            bg="#f0f0f0"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_input(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory(
            title="Select ML Project Directory",
            initialdir=Path.home()
        )
        if directory:
            self.input_path.set(directory)
            self.log(f"✓ Selected input: {directory}")

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_path.get() or Path.home()
        )
        if directory:
            self.output_path.set(directory)
            self.log(f"✓ Selected output: {directory}")

    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)

    def validate_inputs(self):
        """Validate input and output paths"""
        input_dir = Path(self.input_path.get())
        output_dir = Path(self.output_path.get())

        if not self.input_path.get():
            messagebox.showerror(
                "Input Required",
                "Please select your ML project directory"
            )
            return False

        if not input_dir.exists():
            messagebox.showerror(
                "Invalid Input",
                f"Directory does not exist:\n{input_dir}"
            )
            return False

        if not self.output_path.get():
            messagebox.showerror(
                "Output Required",
                "Please select an output directory"
            )
            return False

        return True

    def start_scan(self):
        """Start the compliance scan"""
        if self.scan_running:
            messagebox.showwarning(
                "Scan in Progress",
                "A scan is already running. Please wait for it to complete."
            )
            return

        if not self.validate_inputs():
            return

        # Confirm before starting
        response = messagebox.askyesno(
            "Start Scan",
            "This will scan your ML project for EU AI Act compliance.\n\n"
            "The scan runs locally and no data is uploaded.\n\n"
            "Continue?"
        )

        if not response:
            return

        # Run scan in background thread
        self.scan_running = True
        self.scan_button.config(state=tk.DISABLED, bg="#ccc")
        self.progress_bar.start()

        thread = threading.Thread(target=self.run_scan_thread, daemon=True)
        thread.start()

    def run_scan_thread(self):
        """Run the scan in a background thread"""
        try:
            input_dir = Path(self.input_path.get())
            output_dir = Path(self.output_path.get())

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            self.log("=" * 60)
            self.log("🔍 Starting EU AI Act Compliance Scan")
            self.log("=" * 60)
            self.update_status("Scanning...")

            # Load rulepack
            self.log("📋 Loading EU AI Act rulepack...")
            rulepack_path = AGENT_DIR / "rulepacks" / "euai_core_v1.yaml"

            if not rulepack_path.exists():
                self.log("⚠️  Rulepack not found, using default rules")
                rulepack_path = AGENT_DIR / "rulepacks" / "default_rules.yaml"

            rp = load_rulepack(rulepack_path)
            self.log(f"✓ Loaded rulepack: {rp.get('pack_id', 'unknown')}")

            # Run scan
            self.log(f"🔍 Scanning project: {input_dir}")
            self.log("   This may take a few minutes...")

            results = run_scan(input_dir, iter_rules(rp))

            # Save results
            self.log("💾 Saving results...")

            # JSON report
            json_path = output_dir / "compliance_findings.json"
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
            self.log(f"✓ JSON report: {json_path}")

            # PDF report
            try:
                pdf_path = output_dir / "compliance_report.pdf"
                render_pdf(results, pdf_path)
                self.log(f"✓ PDF report: {pdf_path}")
            except Exception as e:
                self.log(f"⚠️  PDF generation skipped: {str(e)}")

            # Summary
            summary = results.get("summary", {})
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            total = passed + failed

            self.log("=" * 60)
            self.log("📊 SCAN COMPLETE")
            self.log("=" * 60)
            self.log(f"Total checks: {total}")
            self.log(f"✓ Passed: {passed}")
            self.log(f"✗ Failed: {failed}")
            self.log(f"📁 Results saved to: {output_dir}")
            self.log("=" * 60)

            self.update_status("Scan completed successfully")

            # Show completion dialog
            self.root.after(0, lambda: self.show_completion_dialog(output_dir, passed, failed))

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            self.update_status("Scan failed")
            self.root.after(0, lambda: messagebox.showerror(
                "Scan Failed",
                f"An error occurred during the scan:\n\n{str(e)}"
            ))

        finally:
            self.scan_running = False
            self.root.after(0, lambda: self.scan_button.config(
                state=tk.NORMAL,
                bg="#10b981"
            ))
            self.root.after(0, self.progress_bar.stop)

    def show_completion_dialog(self, output_dir, passed, failed):
        """Show scan completion dialog"""
        total = passed + failed
        compliance_rate = (passed / total * 100) if total > 0 else 0

        message = (
            f"Scan completed successfully!\n\n"
            f"Results:\n"
            f"  • Total checks: {total}\n"
            f"  • Passed: {passed}\n"
            f"  • Failed: {failed}\n"
            f"  • Compliance rate: {compliance_rate:.1f}%\n\n"
            f"Reports saved to:\n{output_dir}\n\n"
            f"Would you like to open the output folder?"
        )

        response = messagebox.askyesno(
            "Scan Complete",
            message
        )

        if response:
            # Open output directory in Finder (macOS)
            os.system(f'open "{output_dir}"')


def main():
    """Main entry point"""
    root = tk.Tk()

    # Set app icon if available
    try:
        icon_path = AGENT_DIR / "assets" / "icon.png"
        if icon_path.exists():
            root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
    except:
        pass

    app = CompliSenseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()