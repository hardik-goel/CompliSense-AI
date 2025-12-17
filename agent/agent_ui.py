import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback

from agent.agent_runner import run_agent
from agent.config import AgentConfig


class CompliSenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CompliSense AI")
        self.root.geometry("520x420")

        self.model_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")

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
        ttk.Button(
            self.root,
            text="Run Compliance Scan",
            command=self.start_scan
        ).pack(pady=20)

        # Progress
        ttk.Label(self.root, textvariable=self.status, foreground="blue").pack()
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=40, pady=10)

        ttk.Label(
            self.root,
            text="Privacy: All analysis runs locally. No uploads unless enabled.",
            font=("Helvetica", 9)
        ).pack(pady=10)

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

        self.progress.start()
        self.status.set("Running compliance checks...")

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        try:
            config = AgentConfig(upload_enabled=False, llm_enabled=False)

            result = run_agent(
                model_root=self.model_path.get(),
                out_dir=self.out_path.get(),
                rulepack_path="rulepacks/euai_core_v1.yaml",
                progress_callback=self._update_status,
                config=config
            )

            self.root.after(0, lambda: self._on_success(result))

        except Exception as e:
            traceback.print_exc()
            self.root.after(0, lambda: self._on_error(e))

    def _update_status(self, msg):
        self.root.after(0, lambda: self.status.set(msg))

    def _on_success(self, result):
        self.progress.stop()
        self.status.set("Scan complete")

        messagebox.showinfo(
            "Completed",
            f"Compliance scan finished.\n\n"
            f"PDF: {result['pdf']}\n"
            f"Dashboard: {result['dashboard']}"
        )

    def _on_error(self, e):
        self.progress.stop()
        self.status.set("Error occurred")
        messagebox.showerror("Error", str(e))

    def guided_start(self):
        # Step 1: ask for input folder
        messagebox.showinfo(
            "Select AI / ML Model Folder",
            "Please select the folder containing your AI/ML model.\n\n"
            "This folder may contain:\n"
            "• .pkl / .onnx / model files\n"
            "• training scripts\n"
            "• logs or documentation"
        )

        model = filedialog.askdirectory(title="Select AI / ML Model Folder")
        if not model:
            self.status.set("Cancelled.")
            return
        self.model_path.set(model)

        # Step 2: ask for output folder
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
            self.status.set("Cancelled.")
            return
        self.out_path.set(out)

        # Step 3: auto-run
        self.start_scan()


def run():
    root = tk.Tk()
    app = CompliSenseApp(root)
    root.after(300, app.guided_start)
    root.mainloop()


if __name__ == "__main__":
    run()
