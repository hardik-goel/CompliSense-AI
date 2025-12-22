import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread

from agent.scanner import run_scan
from agent.rules.loader import load_rulepack  # your existing loader


class CompliSenseUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CompliSense AI Agent")

        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Idle")

        ttk.Label(root, text="CompliSense AI Compliance Scan").pack(pady=10)

        self.progress = ttk.Progressbar(
            root,
            length=400,
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(
            root,
            textvariable=self.status_var
        )
        self.status_label.pack(pady=5)

        ttk.Button(
            root,
            text="Select Project Folder & Scan",
            command=self.start_scan
        ).pack(pady=10)

    # -----------------------------
    # Progress callback
    # -----------------------------
    def on_progress(self, done, total, rule_id):
        pct = int((done / total) * 100)
        self.progress_var.set(pct)
        self.status_var.set(
            f"Running {rule_id} ({done}/{total})"
        )

    # -----------------------------
    # Scan runner
    # -----------------------------
    def start_scan(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        root_path = Path(folder)
        rules = load_rulepack()

        def worker():
            try:
                run_scan(
                    root=root_path,
                    rules=rules,
                    progress_cb=self.on_progress
                )
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Completed",
                        "Compliance scan completed.\nResults written to complisense_output/"
                    )
                )
            except Exception as exc:
                err_msg = str(exc)
                self.root.after(
                    0,
                    lambda msg=err_msg: messagebox.showerror(
                        "Scan failed",
                        msg
                    )
                )

        Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = CompliSenseUI(root)
    root.mainloop()
