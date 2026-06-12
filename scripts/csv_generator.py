import csv
import sys
import os
import urllib.request
import re
import concurrent.futures

def get_title(url, fallback_name):
    try:
        # Menambahkan header User-Agent agar tidak diblokir
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # Mencari tag <title>
            match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Hapus spasi berlebih atau newline dalam title
                title = " ".join(title.split())
                if title:
                    return title
    except Exception:
        pass
    return fallback_name

def process_domain(line):
    domain = line.strip()
    if not domain:
        return None
        
    url = domain
    if not url.startswith('http://') and not url.startswith('https://'):
        url = f"https://{domain}"
        
    fallback_name = domain.replace('https://', '').replace('http://', '').strip('/')
    
    # Ambil judul dari web, jika gagal gunakan fallback_name
    name = get_title(url, fallback_name)
    
    # Maksimal panjang nama untuk CSV agar tidak terlalu panjang
    if len(name) > 80:
        name = name[:77] + '...'
        
    return [name, url, 'true']

def generate_csv(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} tidak ditemukan!")
        print("Silakan buat file teks berisi daftar domain (satu baris per domain).")
        return

    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    valid_domains = 0
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        # Tulis Header
        writer.writerow(['name', 'url', 'is_active'])
        
        print(f"Memproses {len(lines)} baris... (Mengambil judul website, ini mungkin butuh beberapa detik)")
        
        # Proses menggunakan thread pool untuk paralelisasi request HTTP
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(process_domain, lines))
            
            for row in results:
                if row:
                    writer.writerow(row)
                    valid_domains += 1
            
    print(f"Berhasil! {valid_domains} domain telah dikonversi dan disimpan ke: {output_file}.")
    print("Sekarang Anda bisa mengunggah file CSV ini melalui tombol Import di Web UI.")

if __name__ == '__main__':
    input_txt = 'daftar_domain_mentah.txt'
    output_csv = 'siap_import.csv'
    
    if not os.path.exists(input_txt):
        with open(input_txt, 'w', encoding='utf-8') as f:
            f.write("google.com\n")
            f.write("https://github.com\n")
            f.write("jatengprov.go.id\n")
        print(f"File contoh '{input_txt}' telah dibuat otomatis.")
        print(f"Buka file tersebut, hapus isinya, ganti dengan {input_txt} milik Anda (Paste 400+ list domain ke sana).")
        print(f"Lalu jalankan script ini kembali.")
    else:
        generate_csv(input_txt, output_csv)
