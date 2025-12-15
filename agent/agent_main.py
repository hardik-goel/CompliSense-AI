# agent/agent_main.py
import argparse
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import sys
import os
import uvicorn

# Local imports
from agent.api_handlers import app as agent_app

def start_uvicorn():
    uvicorn.run(agent_app, host="127.0.0.1", port=32000, log_level="info")

def run_headless(args):
    # CLI-only run: POST to local API (self-contained)
    import requests, json
    payload = {
        "model_root": args.model_root,
        "output_dir": args.output_dir,
        "rulepack_source": args.rulepack_source,
        "rulepack_path": args.rulepack_path,
        "rulepack_url": args.rulepack_url,
        "upload_summary": args.upload_summary,
        "saas_url": args.saas_url,
        "saas_token": args.saas_token
    }
    r = requests.post("http://127.0.0.1:32000/run", json=payload, timeout=1200)
    print("Response:", r.status_code, r.text)

def run_with_gui():
    # Minimal Tkinter UI to prompt paths, then call /run
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import requests, json

    root = tk.Tk()
    root.title("CompliSense Agent")
    root.geometry("560x260")

    tk.Label(root, text="Model root path:").pack()
    model_entry = tk.Entry(root, width=80)
    model_entry.pack()
    def choose_model():
        p = filedialog.askdirectory(title="Select model root")
        if p: model_entry.delete(0,'end'); model_entry.insert(0, p)
    tk.Button(root, text="Browse", command=choose_model).pack()

    tk.Label(root, text="Output directory:").pack()
    out_entry = tk.Entry(root, width=80)
    out_entry.pack()
    def choose_out():
        p = filedialog.askdirectory(title="Select output dir")
        if p: out_entry.delete(0,'end'); out_entry.insert(0, p)
    tk.Button(root, text="Browse", command=choose_out).pack()

    # Simple checkbox for upload summary
    upload_var = tk.BooleanVar(value=False)
    tk.Checkbutton(root, text="Upload summary to SaaS", variable=upload_var).pack()

    # If uploading, provide fields for SaaS URL and token
    tk.Label(root, text="SaaS URL (optional):").pack()
    saas_entry = tk.Entry(root, width=80)
    saas_entry.pack()
    tk.Label(root, text="SaaS token (optional):").pack()
    token_entry = tk.Entry(root, width=80)
    token_entry.pack()

    def on_run():
        model_root = model_entry.get().strip()
        output_dir = out_entry.get().strip()
        upload_summary = upload_var.get()
        saas_url = saas_entry.get().strip() or None
        saas_token = token_entry.get().strip() or None
        if not model_root or not output_dir:
            messagebox.showerror("Missing paths", "Please select both model root and output directory")
            return
        payload = {
            "model_root": model_root,
            "output_dir": output_dir,
            "rulepack_source": "embed",
            "upload_summary": upload_summary,
            "saas_url": saas_url,
            "saas_token": saas_token
        }
        try:
            resp = requests.post("http://127.0.0.1:32000/run", json=payload, timeout=3600)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Scan completed. Check output dir for findings.json and audit_report.pdf")
            else:
                messagebox.showerror("Scan failed", f"{resp.status_code}: {resp.text}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Run Scan", command=on_run, bg="#2E7D32", fg="white").pack(pady=10)

    root.mainloop()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nogui", action="store_true", help="Run without GUI (headless)")
    parser.add_argument("--model-root", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--rulepack-source", default="embed")
    parser.add_argument("--rulepack-path", default=None)
    parser.add_argument("--rulepack-url", default=None)
    parser.add_argument("--upload-summary", action="store_true")
    parser.add_argument("--saas-url", default=None)
    parser.add_argument("--saas-token", default=None)
    args = parser.parse_args()

    # Start local API server in background thread
    t = threading.Thread(target=start_uvicorn, daemon=True)
    t.start()
    time.sleep(1.0)  # give server time to come up

    if args.nogui:
        # If model_root/output-dir provided, call run directly
        if not args.model_root or not args.output_dir:
            print("Provide --model-root and --output-dir in nogui mode")
            sys.exit(1)
        run_headless(args)
    else:
        run_with_gui()

if __name__ == "__main__":
    main()
