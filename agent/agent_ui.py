import tkinter as tk
from tkinter import filedialog, messagebox
from agent.agent_runner import run_agent

def run():
    root = tk.Tk()
    root.withdraw()

    model_root = filedialog.askdirectory(title="Select ML Model / Data Directory")
    if not model_root:
        return

    out_dir = filedialog.askdirectory(title="Select Output Directory")
    if not out_dir:
        return

    result = run_agent(
        model_root=model_root,
        out_dir=out_dir,
        rulepack_path="rulepacks/euai_core_v1.yaml"
    )

    messagebox.showinfo(
        "CompliSense AI",
        f"Scan complete!\n\nPDF: {result['pdf']}\nJSON: {result['json']}"
    )

if __name__ == "__main__":
    run()
