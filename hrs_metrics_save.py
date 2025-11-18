import requests
import json
import re
import os
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# ----------------------------
# Globals for cancellation & logs
# ----------------------------
stop_scraping = False
log_lines = []

def sanitize_filename(name):
    invalid = r'[<>:"/\\|?*]'
    return re.sub(invalid, '_', name)

def save_to_txt(title, name, text, params, folder_path):
    os.makedirs(folder_path, exist_ok=True)
    file_name = sanitize_filename(f"{title}-{name}.sql")
    file_path = os.path.join(folder_path, file_name)
    f_text = f"/*{params}*/\n\n\n{text}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f_text)

# ----------------------------
# Scraping function (Threaded)
# ----------------------------
def do_scrape(email, password, progress_bar, progress_label, progress_window, log_text):
    global stop_scraping, log_lines
    stop_scraping = False
    log_lines = []

    failed_url = []
    session = requests.Session()

    # LOGIN
    login_url = "http://hrs-home.brmh.org/api/auth/login"
    payload = {"email": email, "password": password}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "http://hrs-home.brmh.org",
        "Referer": "http://hrs-home.brmh.org/user/signin",
        "User-Agent": "Mozilla/5.0"
    }

    res = session.post(login_url, json=payload, headers=headers)
    if res.status_code != 200:
        messagebox.showerror("Login Failed", "Invalid email or password.")
        progress_window.destroy()
        return

    data = res.json()
    access_token = data["accessToken"]
    refresh_token = data["refreshToken"]

    # Pick folder
    folder_path = filedialog.askdirectory(title="Pick folder to save results")
    if not folder_path:
        messagebox.showwarning("Cancelled", "No folder selected.")
        progress_window.destroy()
        return

    session.cookies.set("accessToken", access_token, domain="hrs-metrics.brmh.org")
    session.cookies.set("refreshToken", refresh_token, domain="hrs-metrics.brmh.org")

    total = 1700

    for i in range(1, total + 1):
        if stop_scraping:  # Check for cancellation
            log_lines.append("Scraping canceled by user.")
            break

        mypage_url = f"http://hrs-metrics.brmh.org/metrics/{i}?tab=query"
        try:
            res2 = session.get(mypage_url, headers={"User-Agent": "Mozilla/5.0"})
        except Exception as e:
            log_lines.append(f"Request failed: {mypage_url} - {str(e)}")
            continue

        # Update progress
        percent = int((i / total) * 100)
        progress_bar["value"] = percent
        progress_label.config(text=f"{percent}%")
        progress_bar.update()

        log_lines.append(f"Processing: {mypage_url}")
        log_text.config(state="normal")
        log_text.insert(tk.END, f"{mypage_url}\n")
        log_text.see(tk.END)
        log_text.config(state="disabled")

        if res2.history == []:
            soup = BeautifulSoup(res2.text, "html.parser")
            scripts = soup.find_all("script")

            for script in scripts:
                if not script.text.strip():
                    continue
                try:
                    raw = script.text
                    start = raw.find("{")
                    end = raw.rfind("}") + 1
                    json_text = raw[start:end]

                    json_text = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', json_text)
                    json_text = json_text.rstrip(";")
                    data = json.loads(json_text)

                    title = data["props"]["pageProps"]["currMetricsInfo"]["category"]["name"]
                    query_data = data["props"]["pageProps"]["queries"]

                    for q in query_data:
                        params = q["parameters"]
                        name = q["queryName"]
                        text = q["queryText"]
                        save_to_txt(title, name, text, params, folder_path)

                except Exception as e:
                    failed_url.append(mypage_url)
                    log_lines.append(f"Failed: {mypage_url} - {str(e)}")
                    log_text.config(state="normal")
                    log_text.insert(tk.END, f"Failed: {mypage_url}\n")
                    log_text.see(tk.END)
                    log_text.config(state="disabled")


    if not stop_scraping:
        messagebox.showinfo("Done", "Scraping completed!")
    if failed_url:
        print("Failed URLs:", failed_url)


# ----------------------------
# Login UI
# ----------------------------
def start_ui():
    global stop_scraping

    root = tk.Tk()
    root.title("HRS Login")
    root.geometry("350x250")
    root.resizable(False, False)

    tk.Label(root, text="HRS Email:").pack(pady=(20, 5))
    entry_email = tk.Entry(root, width=30)
    entry_email.pack()

    tk.Label(root, text="Password:").pack(pady=(10, 5))
    entry_password = tk.Entry(root, show="*", width=30)
    entry_password.pack()

    show_pass_var = tk.BooleanVar(value=False)

    def toggle_password():
        if show_pass_var.get():
            entry_password.config(show="")
        else:
            entry_password.config(show="*")

    tk.Checkbutton(root, text="Show Password", variable=show_pass_var, command=toggle_password).pack(pady=5)

    def handle_login():
        email = entry_email.get().strip()
        password = entry_password.get().strip()

        if not email or not password:
            messagebox.showwarning("Missing Info", "Email and password required.")
            return

        # Test login before opening progress window
        test_session = requests.Session()
        login_url = "http://hrs-home.brmh.org/api/auth/login"
        res = test_session.post(login_url, json={"email": email, "password": password},
                                headers={"Content-Type": "application/json"})
        if res.status_code != 200:
            messagebox.showerror("Login Failed", "Email or password is incorrect.")
            return

        root.destroy()

        # --- Progress Window ---
        progress_window = tk.Tk()
        progress_window.title("Scraping Progress")
        progress_window.geometry("500x400")
        progress_window.resizable(False, False)

        tk.Label(progress_window, text="Scraping Metrics...", font=("Arial", 12)).pack(pady=5)

        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=400, mode="determinate")
        progress_bar.pack(pady=5)

        progress_label = tk.Label(progress_window, text="0%")
        progress_label.pack(pady=5)

        # --- Log Viewer ---
        tk.Label(progress_window, text="Logs:").pack()
        log_text = tk.Text(progress_window, height=15, width=60, state="disabled")
        log_text.pack(pady=5)

        # --- Cancel Button ---
        def cancel_scraping():
            global stop_scraping
            stop_scraping = True
            messagebox.showinfo("Cancelled", "Scraping Cancelled")
            progress_window.destroy()

        tk.Button(progress_window, text="Cancel Scraping", command=cancel_scraping, bg="red", fg="white").pack(pady=5)

        # Start scraping in thread
        threading.Thread(target=do_scrape, args=(email, password, progress_bar, progress_label, progress_window, log_text), daemon=True).start()

        progress_window.mainloop()

    tk.Button(root, text="Login", width=15, command=handle_login).pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    start_ui()
