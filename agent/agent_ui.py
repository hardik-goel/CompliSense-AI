import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
import threading
import traceback

from agent.agent_runner import run_agent
from agent.config import AgentConfig

import logging

logging.basicConfig(
    filename="complisense_agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


class CompliSenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CompliSense AI")
        self.root.geometry("520x420")

        self.model_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.cancel_event = threading.Event()
        self.scanned_files = []
        self._build_ui()

    def _build_ui(self):
        ttk.Label(
            self.root,
            text="CompliSense AI",
            font=("Helvetica", 18, "bold")
        ).pack(pady=10)

        ttk.Label(
            self.root,
            text="Run EU AI Act compliance checks locally.\nNo data ever leaves your system.",
            wraplength=480,
            justify="center"
        ).pack(pady=10)

        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=30, pady=10)

        # Model selector
        ttk.Label(
            frame,
            text="AI / ML Project Folder\n"
                 "Choose the folder containing your model (.pkl/.onnx), "
                 "training code, or any available artifacts.",
            wraplength=420,
            justify="left"
        ).pack(anchor="w")
        ttk.Entry(frame, textvariable=self.model_path).pack(fill="x")
        ttk.Button(frame, text="Browse", command=self.choose_model).pack(pady=5)

        # Output selector
        ttk.Label(
            frame,
            text="Output Folder\n"
                 "Reports will be saved here:\n"
                 "• audit_report.pdf\n"
                 "• dashboard.html\n"
                 "• findings.json",
            wraplength=420,
            justify="left"
        ).pack(anchor="w", pady=(10, 0))
        ttk.Entry(frame, textvariable=self.out_path).pack(fill="x")
        ttk.Button(frame, text="Browse", command=self.choose_output).pack(pady=5)

        # Run button
        btns = ttk.Frame(self.root)
        btns.pack(pady=10)
        ttk.Button(btns, text="Run Scan", command=self.start_scan).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel Scan", command=self.cancel_scan).pack(side="left", padx=5)

        # Progress
        ttk.Label(self.root, textvariable=self.status, foreground="blue").pack()
        self.progress = ttk.Progressbar(
            self.root,
            mode="determinate",
            maximum=100
        )
        self.progress.pack(fill="x", padx=40, pady=10)

        ttk.Label(
            self.root,
            text="Privacy: All analysis runs locally. No uploads unless enabled.",
            font=("Helvetica", 9)
        ).pack(anchor="w", padx=40)

        self.file_list = tk.Listbox(self.root, height=8)
        self.file_list.pack(fill="both", padx=40, pady=5)

    def guided_start(self):
        # Privacy notice
        messagebox.showinfo(
            "Privacy Notice",
            "All analysis runs entirely on your system.\n\n"
            "No model files, datasets, or source code are uploaded."
        )

        # Step 1: Input folder
        messagebox.showinfo(
            "Select AI / ML Model Folder",
            "Please select the folder containing your AI/ML model.\n\n"
            "This may include:\n"
            "• .pkl / .onnx files\n"
            "• training scripts\n"
            "• logs or documentation"
        )
        model = filedialog.askdirectory(title="Select AI / ML Model Folder")
        if not model:
            self.status.set("Cancelled by user.")
            return
        self.model_path.set(model)

        # Step 2: Output folder
        messagebox.showinfo(
            "Select Output Folder",
            "Please select a folder where compliance results will be saved.\n\n"
            "Generated files:\n"
            "• audit_report.pdf\n"
            "• dashboard.html\n"
            "• findings.json"
        )
        out = filedialog.askdirectory(title="Select Output Folder")
        if not out:
            self.status.set("Cancelled by user.")
            return
        self.out_path.set(out)

        # Auto-run scan
        self.start_scan()

    def choose_model(self):
        path = filedialog.askdirectory(title="Select AI / ML Project Folder")
        if path:
            self.model_path.set(path)

    def choose_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.out_path.set(path)

    def start_scan(self):
        if not self.model_path.get() or not self.out_path.get():
            messagebox.showerror("Missing input", "Please select both folders.")
            return

        self.cancel_event.clear()
        self.progress["value"] = 0
        self.file_list.delete(0, tk.END)
        self.status.set("Running compliance checks...")

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _handle_progress(self, payload):
        def update():
            event = payload.get("event")

            if event == "FILES_DISCOVERED":
                self.file_list.delete(0, tk.END)
                for f in payload["files"]:
                    self.file_list.insert(tk.END, f)

            elif event == "RULE_START":
                pct = int((payload["index"] - 1) / payload["total"] * 100)
                self.progress["value"] = pct
                self.status.set(f"Running {payload['rule_id']}")

            elif event == "RULE_END":
                pct = int(payload["index"] / payload["total"] * 100)
                self.progress["value"] = pct

            elif event == "SCAN_CANCELLED":
                self.status.set("Scan cancelled")
                self.progress["value"] = 0

            elif event == "SCAN_COMPLETE":
                self.progress["value"] = 100
                self.status.set("Scan complete")

        self.root.after(0, update)
    def cancel_scan(self):
        self.cancel_event.set()
        self.status.set("Cancelling scan…")

    def _on_success(self, result):
        self.progress.stop()
        self.status.set("Scan complete")

        messagebox.showinfo(
            "Completed",
            f"Compliance scan finished.\n\n"
            f"PDF: {result['pdf']}\n"
            f"Dashboard: {result['dashboard']}"
        )
        webbrowser.open(f"file://{result['dashboard']}")

    def _on_error(self, e):
        self.progress.stop()
        self.status.set("Error occurred")
        messagebox.showerror("Error", str(e))

    def _run_scan(self):
        try:
            config = AgentConfig(upload_enabled=False, llm_enabled=False)

            result = run_agent(
                model_root=self.model_path.get(),
                out_dir=self.out_path.get(),
                rulepack_path="euai_core_v1.yaml",
                progress_callback=self._handle_progress,
                config=config
            )

            self.root.after(0, lambda: self._on_success(result))

        except Exception as e:
            traceback.print_exc()
            logging.exception("Agent failed")
            self.root.after(0, lambda err=e: self._on_error(err))

    def _update_status(self, msg):
        def update():
            self.status.set(msg)
            self.progress.step(20)

        self.root.after(0, update)


def run():
    root = tk.Tk()
    app = CompliSenseApp(root)
    root.after(300, app.guided_start)
    root.mainloop()


if __name__ == "__main__":
    run()
