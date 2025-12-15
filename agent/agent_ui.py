import tkinter as tk
from tkinter import filedialog, messagebox

from agent.agent_runner import run_agent
from agent.config import AgentConfig


def run():
    app = tk.Tk()
    app.withdraw()

    # -------- WELCOME --------
    messagebox.showinfo(
        "Welcome to CompliSense AI",
        "This tool checks your AI/ML system for EU AI Act compliance.\n\n"
        "You will be asked to:\n"
        "1. Select the folder containing your AI/ML model or project\n"
        "2. Select a folder where compliance reports will be saved\n\n"
        "No data leaves your system."
    )

    # -------- INPUT --------
    messagebox.showinfo(
        "Step 1: Select AI/ML Project Folder",
        "Select the folder that contains your AI/ML system.\n\n"
        "Examples:\n"
        "• Model files\n"
        "• Dataset documentation\n"
        "• Training scripts or logs\n\n"
        "This folder will only be READ."
    )

    model_root = filedialog.askdirectory(
        title="Select AI / ML Project Folder"
    )
    if not model_root:
        messagebox.showwarning("Cancelled", "No input folder selected. Exiting.")
        return

    # -------- OUTPUT --------
    messagebox.showinfo(
        "Step 2: Select Output Folder",
        "Select a folder where the compliance outputs will be saved.\n\n"
        "The agent will generate:\n"
        "• PDF compliance report\n"
        "• Interactive dashboard (HTML)\n"
        "• JSON summary"
    )

    out_dir = filedialog.askdirectory(
        title="Select Output Folder for Reports"
    )
    if not out_dir:
        messagebox.showwarning("Cancelled", "No output folder selected. Exiting.")
        return

    # -------- PRIVACY --------
    messagebox.showinfo(
        "Privacy & Security",
        "All checks run locally on your machine.\n\n"
        "No source code, model files, or datasets are uploaded."
    )

    # -------- RUN AGENT --------
    config = AgentConfig(upload_enabled=False)

    result = run_agent(
        model_root=model_root,
        out_dir=out_dir,
        rulepack_path="rulepacks/euai_core_v1.yaml",
        config=config
    )

    # -------- DONE --------
    messagebox.showinfo(
        "Scan Complete",
        f"Compliance scan completed successfully.\n\n"
        f"PDF Report:\n{result['pdf']}\n\n"
        f"Dashboard:\n{result['dashboard']}\n\n"
        "You can share these files internally or with auditors."
    )


if __name__ == "__main__":
    run()
