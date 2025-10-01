import os
import re
import sys
import asyncio
import glob
import json
from datetime import timedelta, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

# Mengambil TOKEN dari environment variable
# Ini lebih aman karena token tidak ditulis langsung di dalam kode
TOKEN = os.getenv("TOKEN")

# Tentukan jalur dasar, yaitu satu folder di atas lokasi skrip ini
# Karena main.py berada di src/, ini akan mengarah ke folder utama botmu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tentukan folder tempat file user disimpan
DATA_FOLDER = os.path.join(BASE_DIR, "user")
# Gabungkan dengan nama file dasar
DOMAIN_FILE_BASE = os.path.join(DATA_FOLDER, "domains")
SCHEDULE_FILE_BASE = os.path.join(DATA_FOLDER, "schedule")
# Interval pengecekan otomatis dalam detik (1 jam)
CHECK_INTERVAL_SECONDS = 3600

# --- FUNGSI UNTUK MENGELOLA FILE DOMAIN PER PENGGUNA ---

def get_domain_filename(chat_id, username=None):
    """
    Membuat nama file unik untuk setiap chat_id, termasuk username untuk kemudahan
    identifikasi manual.
    """
    if username:
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-')).rstrip()
        return os.path.join(DATA_FOLDER, f"domains_{safe_username}_{chat_id}.txt")
    else:
        return os.path.join(DATA_FOLDER, f"domains_{chat_id}.txt")

def load_domains(chat_id, username=None):
    """Membaca daftar domain dari file untuk chat_id tertentu."""
    filename = get_domain_filename(chat_id, username)
    try:
        if not os.path.exists(filename):
            # Mencoba mencari file lama jika format baru tidak ditemukan
            filename_old = os.path.join(DATA_FOLDER, f"domains_{chat_id}.txt")
            if os.path.exists(filename_old):
                os.rename(filename_old, filename)
            else:
                return []
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error membaca file {filename}: {e}")
        return []

def save_domains(domains, chat_id, username=None):
    """Menyimpan daftar domain ke file untuk chat_id tertentu."""
    filename = get_domain_filename(chat_id, username)
    # Pastikan direktori ada sebelum menulis file
    os.makedirs(DATA_FOLDER, exist_ok=True)
    try:
        with open(filename, "w") as f:
            for domain in domains:
                f.write(f"{domain}\n")
    except IOError as e:
        print(f"Error menulis ke file {filename}: {e}")

# --- FUNGSI BARU: MENGELOLA FILE JADWAL PENGECETAN OTOMATIS ---

def get_schedule_filename(chat_id, username=None):
    """Membuat nama file jadwal unik untuk setiap chat_id."""
    if username:
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-')).rstrip()
        return os.path.join(DATA_FOLDER, f"schedule_{safe_username}_{chat_id}.json")
    else:
        return os.path.join(DATA_FOLDER, f"schedule_{chat_id}.json")

def save_schedule(chat_id, username, start_time):
    """Menyimpan waktu mulai job ke file JSON."""
    filename = get_schedule_filename(chat_id, username)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    try:
        with open(filename, 'w') as f:
            json.dump({'start_time': start_time.isoformat()}, f)
    except IOError as e:
        print(f"Error menulis ke file jadwal {filename}: {e}")

def load_schedule(chat_id, username):
    """Membaca waktu mulai job dari file JSON."""
    filename = get_schedule_filename(chat_id, username)
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            return datetime.fromisoformat(data['start_time'])
        return None
    except (IOError, json.JSONDecodeError, KeyError) as e:
        print(f"Error membaca atau memproses file jadwal {filename}: {e}")
        return None

def delete_schedule_file(chat_id, username):
    """Menghapus file jadwal."""
    filename = get_schedule_filename(chat_id, username)
    if os.path.exists(filename):
        os.remove(filename)

# --- FUNGSI UNTUK LOGGING YANG LEBIH RAPI ---
def log_message(username, message):
    """Fungsi pembantu untuk mencetak pesan log dengan format yang konsisten."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] User: {username} | {message}")

# Fungsi inti yang menjalankan proses web scraping dan screenshot
async def _perform_domain_check(domain_names_list, username, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Melakukan pengecekan domain Nawala menggunakan Selenium dan mengirimkan screenshot.
    Fungsi ini dipanggil oleh perintah manual (/cek) dan pengecekan otomatis.
    """
    driver = None
    try:
        # Perubahan di sini: Menggabungkan domain dengan nomor urut
        formatted_domains = [f"{i+1}. {domain}" for i, domain in enumerate(domain_names_list)]
        domain_names_log = "\n".join(formatted_domains)
        
        log_message(username, f"Pengecekan dimulai. Domain:\n{domain_names_log}")

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080") 
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument("--log-level=3") 
        
        log_message(username, "Menginisialisasi browser Chrome...")
        
        # Tentukan jalur ke chromedriver.exe di folder src/
        driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
        
        # Buat objek Service yang menunjuk ke chromedriver.exe
        chrome_service = Service(executable_path=driver_path, service_log_path=os.devnull)
        
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        website_url = "https://nawalacheck.skiddle.id"
        log_message(username, f"Membuka halaman web: {website_url}")
        driver.get(website_url)
        
        wait = WebDriverWait(driver, 20)
        
        log_message(username, "Menunggu kolom input siap...")
        input_field = wait.until(EC.presence_of_element_located((By.ID, "domains")))
        input_field.send_keys("\n".join(domain_names_list)) 
        
        log_message(username, "Menunggu tombol 'Check Domains' siap...")
        check_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Check Domains')]")))
        
        log_message(username, "Mengklik tombol...")
        check_button.click()
        
        log_message(username, "Menunggu hasil pengecekan (15 detik)...")
        await asyncio.sleep(15) 
        
        screenshot_filename = "nawala_check.png"
        log_message(username, "Mengambil screenshot...")
        body_element = driver.find_element(By.TAG_NAME, 'body')
        body_element.screenshot(screenshot_filename)
        
        log_message(username, "Mengirim screenshot ke Telegram...")
        with open(screenshot_filename, "rb") as image_file:
            if update:
                await update.message.reply_photo(photo=InputFile(image_file), caption="Hasil pengecekan domain sudah selesai!")
            else:
                await context.bot.send_photo(chat_id=context.job.chat_id, photo=InputFile(image_file), caption="Hasil pengecekan otomatis domain sudah selesai!")
            
        os.remove(screenshot_filename)
            
    except TimeoutException:
        error_message = "Terjadi error saat mengecek domain. Bot kehabisan waktu saat menunggu elemen di halaman. Coba lagi atau periksa koneksi internetmu."
        if update:
            await update.message.reply_text(error_message)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text=error_message)
        log_message(username, f"ERROR: {error_message}")
    except NoSuchElementException:
        error_message = "Terjadi error saat mengecek domain. Bot tidak dapat menemukan elemen di halaman web."
        if update:
            await update.message.reply_text(error_message)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text=error_message)
        log_message(username, f"ERROR: {error_message}")
    except WebDriverException as e:
        error_message = f"Terjadi error pada WebDriver Selenium. Pastikan semua dependensi sudah terpasang. Error: {e}"
        if update:
            await update.message.reply_text(error_message)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text=error_message)
        log_message(username, f"ERROR WebDriver: {error_message}")
    except Exception as e:
        error_message = f"Terjadi error tak terduga saat mengecek domain. Error: {e}"
        if update:
            await update.message.reply_text(error_message)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text=error_message)
        log_message(username, f"ERROR tak terduga: {e}")
    
    finally:
        if driver:
            driver.quit()
            log_message(username, "Browser ditutup. Proses pengecekan selesai.")

# Fungsi untuk perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.message.from_user.first_name
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /start")
    await update.message.reply_text(
        f'Halo {user_first_name}! Aku adalah bot untuk mengecek domain Nawala.\n'
        'Ketik /cek [domain_mu] untuk memulai.\n'
        '\nBerikut cara untuk mengatur pengecekan otomatis:\n'
        '- /tambah [domain] untuk menambahkan domain dan memulai pengecekan otomatis\n'
        '- /hapus untuk menghapus semua domain\n'
        '- /daftar untuk melihat daftar domain\n'
        '- /status untuk melihat status pengecekan otomatis'
    )
    
# Fungsi untuk perintah /cek (manual)
async def cek_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /cek")
    if not context.args:
        await update.message.reply_text("Silakan masukkan domain setelah perintah /cek. Contoh: /cek cek.com")
        return
    
    domain_names_list = context.args
    await update.message.reply_text(f"Sedang mengecek domain:\n**{'\n'.join(domain_names_list)}**\n... Mohon tunggu sebentar.")
    await _perform_domain_check(domain_names_list, username, update, context)

# Fungsi untuk perintah /tambah
async def tambah_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /tambah")
    if not context.args:
        await update.message.reply_text("Silakan masukkan domain yang ingin ditambahkan. Contoh: /tambah domainbaru.com")
        return
    
    chat_id = update.message.chat_id
    # Menghilangkan spasi ekstra di awal/akhir setiap domain sebelum diproses
    domains_to_add = [arg.strip().lower() for arg in context.args] 
    domains = load_domains(chat_id, username)
    
    added_domains = []
    skipped_domains = []
    
    is_first_domain_added = not domains
    
    for domain in domains_to_add:
        if domain not in domains:
            domains.append(domain)
            added_domains.append(domain)
        else:
            skipped_domains.append(domain)
            
    if added_domains:
        save_domains(domains, chat_id, username)
        added_text = "**" + "**, **".join(added_domains) + "**"
        
        if is_first_domain_added:
            job_name = f"automatic_check_{chat_id}"
            # Menyimpan waktu mulai job ke file
            start_time = datetime.now()
            save_schedule(chat_id, username, start_time)
            
            context.job_queue.run_repeating(cek_otomatis, interval=CHECK_INTERVAL_SECONDS, first=CHECK_INTERVAL_SECONDS, chat_id=chat_id, name=job_name, data={'username': username})
            await update.message.reply_text(f"Domain {added_text} telah ditambahkan dan pengecekan otomatis setiap 1 jam telah diaktifkan!")
        else:
            await update.message.reply_text(f"Domain {added_text} telah ditambahkan ke daftar cek otomatis.")
    
    if skipped_domains:
        skipped_text = "**" + "**, **".join(skipped_domains) + "**"
        await update.message.reply_text(f"Domain {skipped_text} sudah ada di daftar dan dilewati.")


# Fungsi untuk perintah /hapus
async def hapus_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /hapus")
    chat_id = update.message.chat_id
    domains = load_domains(chat_id, username)
    if domains:
        save_domains([], chat_id, username)
        delete_schedule_file(chat_id, username) # Menghapus file jadwal
        
        job_name = f"automatic_check_{chat_id}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
        
        await update.message.reply_text("Semua domain telah berhasil dihapus dari daftar cek otomatis. Jadwal pengecekan otomatis juga telah dibatalkan.")
    else:
        await update.message.reply_text("Daftar domain untuk cek otomatis sudah kosong, tidak ada yang perlu dihapus.")


# Fungsi untuk perintah /daftar
async def lihat_daftar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /daftar")
    chat_id = update.message.chat_id
    domains = load_domains(chat_id, username)
    if domains:
        domain_list_text = "\n".join(domains)
        await update.message.reply_text(f"Daftar domain untuk cek otomatis:\n\n{domain_list_text}")
    else:
        await update.message.reply_text("Daftar domain untuk cek otomatis masih kosong. Gunakan /tambah untuk menambahkannya.")

# Fungsi untuk perintah /status
async def cek_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username or f"user_{update.message.from_user.id}"
    log_message(username, "Perintah /status")
    chat_id = update.message.chat_id
    job_name = f"automatic_check_{chat_id}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    domains = load_domains(chat_id, username)
    
    if current_jobs:
        # Pengecekan otomatis aktif
        next_run_time_utc = current_jobs[0].next_run_time
        next_run_time_local = next_run_time_utc + timedelta(hours=7)
        next_run_time_str = next_run_time_local.strftime("%H:%M:%S")

        status_message = f"Pengecekan otomatis sedang aktif. Pengecekan berikutnya dijadwalkan pada {next_run_time_str}."
        
        if domains:
            domain_list_text = "\n- ".join(domains)
            status_message += f"\n\nDomain yang sedang dipantau:\n- {domain_list_text}"
        else:
            status_message += "\n\nNamun, daftar domain untuk pengecekan otomatis kosong. Gunakan /tambah untuk menambahkan domain."

        await update.message.reply_text(status_message)
    else:
        # Pengecekan otomatis tidak aktif
        await update.message.reply_text("Pengecekan otomatis tidak sedang berjalan. Gunakan perintah /tambah untuk menambahkan domain dan mengaktifkannya.")


# Fungsi yang akan dijalankan oleh JobQueue setiap 1 jam
async def cek_otomatis(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    username = context.job.data.get('username', f"user_{chat_id}")
    
    log_message(username, f"Mulai proses pengecekan otomatis (chat ID: {chat_id})")

    domains_to_check = load_domains(chat_id, username)
    if domains_to_check:
        domain_names_text = "\n".join(domains_to_check)
        await context.bot.send_message(chat_id=chat_id, text=f"Sedang menjalankan pengecekan otomatis untuk domain:\n**{domain_names_text}**\n... Mohon tunggu sebentar.")
        
        await _perform_domain_check(domains_to_check, username, None, context)
    else:
        job_name = f"automatic_check_{chat_id}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
            
        await context.bot.send_message(chat_id=chat_id, text="Daftar domain untuk cek otomatis kosong. Pengecekan otomatis dihentikan.")


def main():
    # Perbaikan di sini: Tambahkan job_queue ke ApplicationBuilder
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cek", cek_domain))
    application.add_handler(CommandHandler("tambah", tambah_domain))
    application.add_handler(CommandHandler("hapus", hapus_domain))
    application.add_handler(CommandHandler("daftar", lihat_daftar))
    application.add_handler(CommandHandler("status", cek_status))
    
    print("Mengecek jadwal otomatis yang tersimpan...")
    
    # Perbaikan jalur: glob sekarang mencari dari BASE_DIR
    file_pattern = os.path.join(DATA_FOLDER, f"domains_*.txt")
    for filename in glob.glob(file_pattern):
        # Perbaikan regex untuk mencocokkan nama file yang ada di folder user
        match = re.search(r"domains_(.+)_(\d+)\.txt$", os.path.basename(filename))
        if match:
            username_from_file = match.group(1)
            chat_id_from_file = int(match.group(2))
            
            domains = load_domains(chat_id_from_file, username_from_file)
            start_time = load_schedule(chat_id_from_file, username_from_file)
            
            if domains and start_time:
                job_name = f"automatic_check_{chat_id_from_file}"
                
                # Hitung waktu tunda yang diperlukan
                now = datetime.now()
                elapsed_time = now - start_time
                next_check_in_seconds = CHECK_INTERVAL_SECONDS - (elapsed_time.total_seconds() % CHECK_INTERVAL_SECONDS)
                
                # Jika waktu tunda negatif (waktu seharusnya sudah lewat), jalankan sekarang
                if next_check_in_seconds < 0:
                    next_check_in_seconds = 0
                
                # Jadwalkan ulang pekerjaan dengan waktu tunda yang sudah dihitung
                application.job_queue.run_repeating(
                    cek_otomatis, 
                    interval=CHECK_INTERVAL_SECONDS, 
                    first=next_check_in_seconds, 
                    chat_id=chat_id_from_file, 
                    name=job_name,
                    data={'username': username_from_file}
                )
                print(f"  -> Menjadwalkan ulang pengecekan untuk user: {username_from_file} (Chat ID: {chat_id_from_file})")
            elif domains and not start_time:
                # Jika file domain ada tapi file jadwal tidak ada, buat jadwal baru
                print(f"  -> File jadwal tidak ditemukan untuk {username_from_file}. Menjadwalkan ulang dengan waktu saat ini.")
                job_name = f"automatic_check_{chat_id_from_file}"
                start_time = datetime.now()
                save_schedule(chat_id_from_file, username_from_file, start_time)
                application.job_queue.run_repeating(
                    cek_otomatis,
                    interval=CHECK_INTERVAL_SECONDS,
                    first=CHECK_INTERVAL_SECONDS,
                    chat_id=chat_id_from_file,
                    name=job_name,
                    data={'username': username_from_file}
                )


    print("Bot sudah berjalan...")
    application.run_polling()

if __name__ == '__main__':
    main()