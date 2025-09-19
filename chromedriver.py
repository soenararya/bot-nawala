import os
import sys
import requests
import zipfile
import io
import shutil
import subprocess

def find_chrome_version():
    """Mencari versi Google Chrome yang terinstal di Windows."""
    try:
        # Perintah untuk mendapatkan versi Chrome dari registry
        output = subprocess.check_output(
            'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version',
            shell=True,
            text=True
        )
        version_line = [line for line in output.split('\n') if 'REG_SZ' in line]
        if version_line:
            full_version = version_line[0].split('REG_SZ')[-1].strip()
            return full_version
    except Exception as e:
        print(f"Gagal menemukan versi Chrome: {e}")
    return None

def download_and_extract_chromedriver(chrome_version):
    """
    Mengunduh chromedriver.exe yang sesuai dengan versi Chrome dan 
    menyimpannya di folder yang sama.
    """
    print("Mencari URL chromedriver yang cocok...")
    
    major_version = chrome_version.split('.')[0]
    
    try:
        # Menggunakan API untuk menemukan versi driver yang cocok
        url_api = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
        response = requests.get(url_api)
        data = response.json()
        
        download_url = None
        for version_info in data['versions']:
            # Cocokkan versi utama
            if version_info['version'].startswith(major_version):
                # Cari URL untuk win64
                for download in version_info['downloads']['chromedriver']:
                    if download['platform'] == 'win64':
                        download_url = download['url']
                        break
            if download_url:
                break
        
        if not download_url:
            print(f"Error: Tidak dapat menemukan chromedriver untuk versi {major_version}. Silakan unduh manual.")
            return False

        print(f"URL ditemukan. Mengunduh dari: {download_url}")
        
        # Mengunduh file zip
        file_request = requests.get(download_url)
        zip_file = zipfile.ZipFile(io.BytesIO(file_request.content))
        
        # Mengekstrak chromedriver.exe ke direktori saat ini
        for member in zip_file.namelist():
            if member.endswith('chromedriver.exe'):
                with open("chromedriver.exe", "wb") as output_file:
                    shutil.copyfileobj(zip_file.open(member), output_file)
                print("chromedriver.exe berhasil diupdate!")
                return True
                
    except Exception as e:
        print(f"Terjadi error saat mengunduh/mengekstrak chromedriver: {e}")
        return False

if __name__ == "__main__":
    print("Mengecek versi Google Chrome...")
    chrome_version = find_chrome_version()
    
    if chrome_version:
        print(f"Versi Chrome yang ditemukan: {chrome_version}")
        if os.path.exists('chromedriver.exe'):
            print("chromedriver.exe sudah ada. Lewati unduhan.")
        else:
            download_and_extract_chromedriver(chrome_version)
    else:
        print("Gagal menemukan versi Chrome. Silakan unduh driver secara manual.")