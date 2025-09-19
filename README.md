# 🤖 BOT TELEGRAM CEK NAWALA

Bot Telegram ini berfungsi untuk mempermudah pengecekan status domain apakah terblokir oleh **Nawala** atau tidak.  
Bot ini dibuat menggunakan library **Python**:  
- `python-telegram-bot`
- `webdriver-manager`  
- `selenium`   

Bot ini memiliki fitur pengecekan otomatis ( Setiap 1 Jam ) dan juga pengecekan manual.

---

## ✨ Fitur-fitur Utama

- **Pengecekan Manual**  
  Pengguna dapat langsung mengecek status domain dengan perintah:  
  ```
  /cek [nama_domain]
  ```

- **Pengecekan Otomatis**  
  Pengguna dapat menambahkan domain ke daftar pemantauan dengan perintah:  
  ```
  /tambah [nama_domain]
  ```  
  Bot akan secara otomatis mengecek status domain setiap 1 jam dan mengirimkan hasilnya.

- **Manajemen Domain**
  - `/tambah` : Menambahkan domain ke daftar pantauan  
  - `/hapus`  : Menghapus semua domain dari daftar pantauan  
  - `/daftar` : Melihat daftar domain yang sedang dipantau  
  - `/status` : Melihat status pengecekan otomatis dan jadwal pengecekan berikutnya  

---

## 🛠 Panduan Instalasi Lengkap

### Langkah 1: Instalasi Python ( Jika Belum Terpasang )

* Pastikan Python sudah terpasang di komputer Anda. Jika belum, ikuti langkah berikut:
   - Buka situs resmi Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Unduh versi Python terbaru untuk sistem operasi Anda (Windows, macOS, atau Linux).
   - Jalankan file instalasi yang sudah diunduh.
   - **PENTING:** Saat proses instalasi, jangan lupa centang kotak *"Add Python to PATH"* agar Python bisa dikenali di Command Prompt atau terminal.

* Setelah Python berhasil terpasang, Anda bisa melanjutkan ke langkah-langkah di bawah.

---

### Langkah 2: Instalasi Git ( Jika Belum Terpasang )

* Untuk mengambil kode dari GitHub, Anda perlu menginstal **Git** terlebih dahulu.
  
  - Buka situs resmi Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)  
  - Pilih versi sesuai sistem operasi Anda (Windows, macOS, atau Linux).  
  - Jalankan file instalasi yang sudah diunduh.  
  - Pada proses instalasi di Windows, **Biarkan Opsi Default**, lalu lanjutkan sampai selesai.  

Untuk mengecek apakah Git sudah terpasang, jalankan perintah berikut di **Command Prompt** atau **Terminal**:  
```bash
git --version
```
Jika berhasil, akan muncul versi Git yang terpasang. Contoh:  
```
git version 2.51.0
```
* Setelah Git berhasil terpasang, Anda bisa melanjutkan ke langkah-langkah di bawah.

---

### Langkah 3: Mengambil Kode dari GitHub

Buka Command Prompt ( CMD ) atau terminal di PC Anda.

```bash
# Gunakan perintah cd untuk masuk ke folder tempat Anda ingin menyimpan proyek. Contoh:
cd C:\Users\NamaAnda\Documents

# Clone repository ini ke komputer Anda dengan perintah berikut:
git clone https://github.com/soenararya/bot-nawala.git

# Masuk ke folder proyek yang baru saja dibuat:
cd bot-nawala
```

---

### Langkah 4: Menambahkan Token Bot

Untuk menjalankan bot, Anda perlu menyediakan token bot dari **@BotFather** di Telegram.

* Setelah di folder ``` bot-nawala> ``` tambahkan Token di terminal.

#### Opsi 1 (Direkomendasikan): Membuat File `.env`
```bash
# Ini akan membuat file .env beserta Token secara otomatis di file proyek.
echo TOKEN=TokenBotAndaDiSini > .env
```

#### Opsi 2 (Untuk Pengujian): Menggunakan Environment Variable
```bash
# Membuat Token hanya aktif selama jendela terminal masih terbuka saja.
set TOKEN=TokenBotAndaDiSini
```

---

### Langkah 5: Menjalankan Bot

Gunakan skrip **mulai.bat** untuk menjalankan bot. Skrip ini akan:  
- Membuat virtual environment  
- Memperbarui pip  
- Menginstal library  
- Menjalankan bot
  
**PASTIKAN TOKEN BOT ANDA SUDAH DI TAMBAHKAN ( LIHAT BAGIAN MENAMBAHKAN TOKEN BOT DI ATAS ).**

```bash
# Jika sudah semua ketik perintah:
mulai.bat
```

Bot Anda sekarang sudah aktif dan siap digunakan di Telegram! 🎉

---
