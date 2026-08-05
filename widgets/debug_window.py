# ===== ✂️ widgets/debug_window.py START ✂️ =====
import tkinter as tk

class JwNavigatorDebugWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JwNavigator Ver2.0 開発窓")
        self.geometry("500x400")
        self.configure(bg="#222222")
        self.attributes("-topmost", True)

        self.log_box = tk.Text(self, bg="#111111", fg="#00ff00", font=("Consolas", 9), bd=0, highlightthickness=0)
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

    def update_pipeline(self, raw, rule, state, event, intent_list, plan_list, executor, perf_dict):
        msg = f"--- PIPELINE STREAM ---\nRaw: {raw}\nRule: {rule}\nState: {state}\nEvent: {event}\nIntent: {intent_list}\nPlan: {plan_list}\nExec: {executor}\n"
        if perf_dict:
            msg += f"Perf(ms) -> Loop:{perf_dict['loop']:.1f} Watch:{perf_dict['watch']:.1f} Parse:{perf_dict['parse']:.1f} GUI:{perf_dict['gui']:.1f}\n"
        self.log_box.delete("1.0", tk.END)
        self.log_box.insert(tk.END, msg)
        self.log_box.see(tk.END)
# ===== ✂️ widgets/debug_window.py END ✂️ =====
