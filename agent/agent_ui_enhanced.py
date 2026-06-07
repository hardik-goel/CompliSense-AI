import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
from pathlib import Path

from agent.agent_runner import run_agent
from agent.config import AgentConfig
from compliance.registry import DEFAULT_RULEPACK_ID

import logging

logging.basicConfig(
    filename="complisense_agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


class CompliSenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CompliSense AI - Regulatory Compliance Scanner")
        self.root.geometry("700x650")
        self.root.configure(bg="#f5f5f5")

        self.model_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready to scan")
        self.current_rule = tk.StringVar(value="")
        self.progress_pct = tk.IntVar(value=0)
        self.cancel_event = threading.Event()
        self.scanned_files = []
        self.scan_running = False
        self._build_ui()

    def _build_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2563eb", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="CompliSense AI",
            font=("Helvetica", 24, "bold"),
            bg="#2563eb",
            fg="white"
        ).pack(pady=15)

        tk.Label(
            header_frame,
            text="Regulatory Compliance Scanner",
            font=("Helvetica", 11),
            bg="#2563eb",
            fg="#e0e7ff"
        ).pack()

        # Main content
        content_frame = tk.Frame(self.root, bg="#f5f5f5", padx=30, pady=20)
        content_frame.pack(fill="both", expand=True)

        # Description
        desc_label = tk.Label(
            content_frame,
            text="Run regulatory compliance checks locally.\nNo data ever leaves your system.",
            font=("Helvetica", 10),
            bg="#f5f5f5",
            fg="#6b7280",
            justify="center"
        )
        desc_label.pack(pady=(0, 20))

        # Input section
        input_frame = tk.LabelFrame(
            content_frame,
            text="Scan Configuration",
            font=("Helvetica", 11, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15
        )
        input_frame.pack(fill="x", pady=(0, 15))

        # Model path
        tk.Label(
            input_frame,
            text="AI / ML Project Folder",
            font=("Helvetica", 10, "bold"),
            bg="#ffffff",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        tk.Label(
            input_frame,
            text="Choose the folder containing your model (.pkl/.onnx), training code, or artifacts.",
            font=("Helvetica", 9),
            bg="#ffffff",
            fg="#6b7280",
            anchor="w",
            wraplength=600
        ).pack(fill="x", pady=(0, 5))
        
        model_entry_frame = tk.Frame(input_frame, bg="#ffffff")
        model_entry_frame.pack(fill="x", pady=(0, 15))
        tk.Entry(model_entry_frame, textvariable=self.model_path, font=("Helvetica", 10)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(model_entry_frame, text="Browse", command=self.choose_model, bg="#2563eb", fg="white", padx=15).pack(side="right")

        # Output path
        tk.Label(
            input_frame,
            text="Output Folder",
            font=("Helvetica", 10, "bold"),
            bg="#ffffff",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        tk.Label(
            input_frame,
            text="Reports will be saved here: audit_report.pdf, dashboard.html, findings.json",
            font=("Helvetica", 9),
            bg="#ffffff",
            fg="#6b7280",
            anchor="w",
            wraplength=600
        ).pack(fill="x", pady=(0, 5))
        
        out_entry_frame = tk.Frame(input_frame, bg="#ffffff")
        out_entry_frame.pack(fill="x")
        tk.Entry(out_entry_frame, textvariable=self.out_path, font=("Helvetica", 10)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(out_entry_frame, text="Browse", command=self.choose_output, bg="#2563eb", fg="white", padx=15).pack(side="right")

        # Progress section
        progress_frame = tk.LabelFrame(
            content_frame,
            text="Scan Progress",
            font=("Helvetica", 11, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15
        )
        progress_frame.pack(fill="x", pady=(0, 15))

        # Status label
        self.status_label = tk.Label(
            progress_frame,
            textvariable=self.status,
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#2563eb",
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 5))

        # Current rule label
        self.rule_label = tk.Label(
            progress_frame,
            textvariable=self.current_rule,
            font=("Helvetica", 9),
            bg="#ffffff",
            fg="#6b7280",
            anchor="w"
        )
        self.rule_label.pack(fill="x", pady=(0, 10))

        # Progress bar with percentage
        progress_bar_frame = tk.Frame(progress_frame, bg="#ffffff")
        progress_bar_frame.pack(fill="x")
        
        self.progress = ttk.Progressbar(
            progress_bar_frame,
            mode="determinate",
            maximum=100,
            length=500
        )
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.progress_label = tk.Label(
            progress_bar_frame,
            text="0%",
            font=("Helvetica", 10, "bold"),
            bg="#ffffff",
            fg="#2563eb",
            width=5
        )
        self.progress_label.pack(side="right")

        # File list
        files_frame = tk.LabelFrame(
            content_frame,
            text="Discovered Files",
            font=("Helvetica", 11, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15
        )
        files_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Scrollable file list
        list_scroll = tk.Scrollbar(files_frame)
        list_scroll.pack(side="right", fill="y")
        
        self.file_list = tk.Listbox(
            files_frame,
            height=8,
            font=("Courier", 9),
            yscrollcommand=list_scroll.set,
            bg="#f9fafb",
            fg="#111827"
        )
        self.file_list.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.file_list.yview)

        # Buttons
        button_frame = tk.Frame(content_frame, bg="#f5f5f5")
        button_frame.pack(fill="x")

        self.run_button = tk.Button(
            button_frame,
            text="▶ Run Scan",
            command=self.start_scan,
            bg="#22c55e",
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.run_button.pack(side="left", padx=(0, 10))

        self.cancel_button = tk.Button(
            button_frame,
            text="✖ Cancel",
            command=self.cancel_scan,
            bg="#ef4444",
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=20,
            pady=10,
            state="disabled",
            cursor="hand2"
        )
        self.cancel_button.pack(side="left")

        # Privacy notice
        privacy_label = tk.Label(
            content_frame,
            text="🔒 Privacy: All analysis runs locally. No data leaves your system.",
            font=("Helvetica", 9),
            bg="#f5f5f5",
            fg="#6b7280"
        )
        privacy_label.pack(pady=(10, 0))

    def choose_model(self):
        path = filedialog.askdirectory(title="Select AI / ML Project Folder")
        if path:
            self.model_path.set(path)
            self.status.set(f"Selected: {Path(path).name}")

    def choose_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.out_path.set(path)
            self.status.set(f"Output: {Path(path).name}")

    def start_scan(self):
        if not self.model_path.get() or not self.out_path.get():
            messagebox.showerror(
                "Missing Input",
                "Please select both:\n• AI/ML Project Folder\n• Output Folder",
                icon="error"
            )
            return

        if not Path(self.model_path.get()).exists():
            messagebox.showerror(
                "Invalid Path",
                f"Project folder does not exist:\n{self.model_path.get()}",
                icon="error"
            )
            return

        if not Path(self.out_path.get()).exists():
            try:
                Path(self.out_path.get()).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror(
                    "Invalid Output Path",
                    f"Cannot create output folder:\n{str(e)}",
                    icon="error"
                )
                return

        self.scan_running = True
        self.cancel_event.clear()
        self.progress["value"] = 0
        self.progress_pct.set(0)
        self.progress_label.config(text="0%")
        self.file_list.delete(0, tk.END)
        self.status.set("Initializing scan...")
        self.current_rule.set("")
        
        # Update button states
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _handle_progress(self, payload):
        """Handle progress updates with better error handling."""
        if isinstance(payload, str):
            payload = {"event": payload}

        if not isinstance(payload, dict):
            return

        def update():
            event = payload.get("event")

            if event == "FILES_DISCOVERED":
                files = payload.get("files", [])
                self.file_list.delete(0, tk.END)
                for f in files[:50]:  # Limit display to 50 files
                    self.file_list.insert(tk.END, f)
                if len(files) > 50:
                    self.file_list.insert(tk.END, f"... and {len(files) - 50} more files")

            elif event == "RULE_START":
                index = payload.get("index", 1)
                total = payload.get("total", 1)
                rule_id = payload.get("rule_id", "rule")

                pct = int((index - 1) / total * 100)
                self.progress["value"] = pct
                self.progress_pct.set(pct)
                self.progress_label.config(text=f"{pct}%")
                self.status.set(f"Scanning rule {index} of {total}")
                self.current_rule.set(f"Current: {rule_id}")

            elif event == "RULE_END":
                index = payload.get("index", 1)
                total = payload.get("total", 1)
                status = payload.get("status", "UNKNOWN")

                pct = int(index / total * 100)
                self.progress["value"] = pct
                self.progress_pct.set(pct)
                self.progress_label.config(text=f"{pct}%")
                
                # Color code status
                if status == "PASS":
                    self.current_rule.set(f"✓ {payload.get('rule_id', 'rule')} - PASSED")
                elif status == "PARTIAL":
                    self.current_rule.set(f"⚠ {payload.get('rule_id', 'rule')} - PARTIAL")
                elif status == "FAIL":
                    self.current_rule.set(f"✗ {payload.get('rule_id', 'rule')} - FAILED")
                else:
                    self.current_rule.set(f"{payload.get('rule_id', 'rule')} - {status}")

            elif event == "SCAN_CANCELLED":
                self.status.set("Scan cancelled by user")
                self.current_rule.set("")
                self.progress["value"] = 0
                self.progress_pct.set(0)
                self.progress_label.config(text="0%")
                self.scan_running = False
                self.run_button.config(state="normal")
                self.cancel_button.config(state="disabled")

            elif event == "SCAN_COMPLETE":
                self.progress["value"] = 100
                self.progress_pct.set(100)
                self.progress_label.config(text="100%")
                self.status.set("Scan complete!")
                self.current_rule.set("All rules evaluated")
                self.scan_running = False
                self.run_button.config(state="normal")
                self.cancel_button.config(state="disabled")

            elif event == "INFO":
                self.status.set(payload.get("message", "Processing..."))

        self.root.after(0, update)

    def cancel_scan(self):
        if self.scan_running:
            self.cancel_event.set()
            self.status.set("Cancelling scan...")
            self.cancel_button.config(state="disabled")

    def _on_success(self, result):
        self.progress["value"] = 100
        self.progress_pct.set(100)
        self.progress_label.config(text="100%")
        self.status.set("✓ Scan completed successfully!")
        self.current_rule.set("")

        # Show success dialog with options
        response = messagebox.askyesno(
            "Scan Complete",
            f"Compliance scan finished successfully!\n\n"
            f"Results saved to:\n{result.get('out_dir', 'output directory')}\n\n"
            f"Would you like to open the dashboard?",
            icon="question"
        )
        
        if response:
            dashboard_path = result.get('dashboard')
            if dashboard_path and Path(dashboard_path).exists():
                webbrowser.open(f"file://{dashboard_path}")
            else:
                messagebox.showinfo(
                    "Dashboard",
                    f"Dashboard file:\n{dashboard_path}\n\n"
                    f"Open this file in your browser to view results."
                )

    def _on_error(self, e):
        self.progress["value"] = 0
        self.progress_pct.set(0)
        self.progress_label.config(text="0%")
        self.status.set("✗ Error occurred")
        self.current_rule.set("")
        self.scan_running = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")

        error_msg = str(e)
        if "FileNotFoundError" in error_msg or "not found" in error_msg.lower():
            error_msg = f"File not found error:\n{error_msg}\n\nPlease check that all required files exist."
        elif "PermissionError" in error_msg:
            error_msg = f"Permission error:\n{error_msg}\n\nPlease check file permissions."
        elif "JSONDecodeError" in error_msg:
            error_msg = f"Invalid JSON file:\n{error_msg}\n\nPlease check your JSON files are valid."

        messagebox.showerror(
            "Scan Error",
            f"An error occurred during the scan:\n\n{error_msg}\n\n"
            f"Check complisense_agent.log for details.",
            icon="error"
        )

    def _run_scan(self):
        try:
            config = AgentConfig(
                upload_enabled=False,
                llm_enabled=False,
                cancel_flag=self.cancel_event
            )

            result = run_agent(
                model_root=self.model_path.get(),
                out_dir=self.out_path.get(),
                rulepack_path=f"{DEFAULT_RULEPACK_ID}.yaml",
                progress_callback=self._handle_progress,
                config=config
            )

            self.root.after(0, lambda: self._on_success(result))

        except Exception as e:
            traceback.print_exc()
            logging.exception("Agent failed")
            self.root.after(0, lambda err=e: self._on_error(err))


def run():
    root = tk.Tk()
    app = CompliSenseApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
