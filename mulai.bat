@echo off
rem Perintah ini memastikan skrip dijalankan dari direktori yang benar.
cd /d "%~dp0"

echo [*] Menjalankan Bot Nawala...
echo.

rem Perintah ini mengecek apakah virtual environment sudah ada.
IF EXIST "venv\Scripts\activate.bat" (
    echo [*] Mengaktifkan virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo [!] Virtual environment tidak ditemukan.
    echo [*] Membuat virtual environment baru...
    python -m venv venv
    echo [*] Mengaktifkan virtual environment yang baru dibuat...
    call venv\Scripts\activate.bat
)

echo.
rem Memeriksa dan memperbarui pip
echo [*] Memeriksa dan memperbarui pip...
python -m pip install --upgrade pip --quiet

echo.
rem Perintah ini mengecek dan menginstal library yang dibutuhkan dengan output yang lebih rapi.
IF EXIST "requirements.txt" (
    echo [*] Memeriksa dan menginstal library dari requirements.txt...
    pip install -r requirements.txt --quiet
    echo [*] Selesai menginstal/memeriksa library!
) ELSE (
    echo [!] File requirements.txt tidak ditemukan!
    echo [!] Tidak bisa menginstal dependency.
)

echo.
rem Menambahkan perintah untuk memperbarui chromedriver secara otomatis
echo [*] Memeriksa dan memperbarui chromedriver...
python src/chromedriver.py

echo.
echo [*] Menjalankan file utama bot (main.py)...
python src/main.py

echo.
echo [*] Proses selesai. Tekan tombol apa saja untuk keluar...
pause