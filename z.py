import requests
import json
import time
import os
import datetime
import sys
import random
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor

# Inisialisasi colorama
init(autoreset=True)

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop ZOOP App")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop")

def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

USED_EMAILS_FILE = "used_emails.json"  # File untuk menyimpan email yang sudah digunakan
VERIFIED_TASKS_FILE = "verified_tasks.json"

def load_emails():
    """Membaca daftar email dari file email.txt"""
    try:
        with open('email.txt', 'r', encoding='utf-8') as file:
            emails = [line.strip() for line in file if line.strip()]
        
        print(Fore.CYAN + f"📧 Email yang terbaca: {emails}")  # Debug print

        if not emails:
            print(Fore.YELLOW + "⚠️ File email.txt ada, tetapi kosong.")

        return emails  # Pastikan selalu mengembalikan list, walaupun kosong
    except FileNotFoundError:
        print(Fore.YELLOW + "⚠️ File email.txt tidak ditemukan, proses tugas daftar ZOOP akan dilewati")
        return []
    except Exception as e:
        print(Fore.RED + f"❌ Error membaca email.txt: {str(e)}")
        return []

def load_email_usage():
    """Memuat daftar email yang sudah digunakan dari file JSON."""
    if not os.path.exists(USED_EMAILS_FILE):
        return {}

    try:
        with open(USED_EMAILS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(Fore.RED + "⚠️ File used_emails.json rusak, mengosongkan data.")
        return {}

def save_email_usage(used_emails):
    """Menyimpan daftar email yang sudah digunakan ke file JSON."""
    with open(USED_EMAILS_FILE, "w") as f:
        json.dump(used_emails, f, indent=4)

def create_header(token=None):
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'cache-control': 'no-cache',
        'connection': 'keep-alive',
        'host': 'tgapi.zoop.com',
        'origin': 'https://tgapp.zoop.com',
        'pragma': 'no-cache',
        'referer': 'https://tgapp.zoop.com/',
        'sec-ch-ua': '"Chromium";v="133", "Microsoft Edge WebView2";v="133", "Not(A:Brand";v="99", "Microsoft Edge";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
    }
    
    if token:
        headers['authorization'] = f'Bearer {token}'
    
    return headers

def login(init_data):
    try:
        url = "https://tgapi.zoop.com/api/oauth/telegram"
        headers = create_header()
        payload = {"initData": init_data}
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            token = data['data']['access_token']
            info = data['data']['information']
            return token, info
        else:
            print(Fore.RED + f"Login gagal! Status code: {response.status_code}")
            return None, None
    except Exception as e:
        print(Fore.RED + f"Error saat login: {str(e)}")
        return None, None

def check_tasks(user_id, token):
    try:
        url = f"https://tgapi.zoop.com/api/tasks/{user_id}"
        headers = create_header(token)
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['data']
        else:
            print(Fore.RED + f"Gagal mengambil data tasks! Status code: {response.status_code}")
            return None
    except Exception as e:
        print(Fore.RED + f"Error saat check tasks: {str(e)}")
        return None

def claim_spin(user_id, token, spin_count):
    """Melakukan spin sebanyak jumlah kesempatan yang tersedia."""
    try:
        if spin_count <= 0:
            print(Fore.YELLOW + "ℹ️ Tidak ada kesempatan spin yang tersedia.")
            return

        for i in range(spin_count):
            current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            url = "https://tgapi.zoop.com/api/users/spin"
            headers = create_header(token)
            payload = {"userId": user_id, "date": current_date}

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                point = data['data']['circle'].get('point', 0)
                print(Fore.GREEN + f"✅ Spin ke-{i+1}/{spin_count}: mendapatkan {point} point")
            else:
                print(Fore.RED + f"❌ Spin ke-{i+1}/{spin_count} gagal! Status code: {response.status_code}")
                break  # Jika ada error, hentikan spin

            time.sleep(2)  # Tambahkan jeda agar tidak terlalu cepat
    except Exception as e:
        print(Fore.RED + f"❌ Error saat spin: {str(e)}")

def mark_daily_spin(user_id, token):
    try:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        url = f"https://tgapi.zoop.com/api/tasks/spinDaily/{user_id}"
        headers = create_header(token)
        payload = {"day": current_date}
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            return True
        else:
            print(Fore.RED + f"Gagal menandai spin harian! Status code: {response.status_code}")
            return False
    except Exception as e:
        print(Fore.RED + f"Error saat menandai spin harian: {str(e)}")
        return False

def claim_daily_reward(user_id, token, index):
    try:
        url = f"https://tgapi.zoop.com/api/tasks/rewardDaily/{user_id}"
        headers = create_header(token)
        payload = {"index": index}
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(Fore.GREEN + "✅ Berhasil klaim reward harian")
            return True
        else:
            print(Fore.RED + f"Gagal klaim reward harian! Status code: {response.status_code}")
            return False
    except Exception as e:
        print(Fore.RED + f"Error saat klaim reward harian: {str(e)}")
        return False

def get_social_tasks(token, user_id):
    try:
        url = "https://tgapi.zoop.com/api/social"
        headers = create_header(token)
        
        # First, get all available tasks
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Filter hanya task yang tidak hidden
            social_tasks = [task for task in data['data'] if task.get('hidden', True) == False]
            
            # Get user's completed tasks to compare
            user_tasks_response = requests.get(f"https://tgapi.zoop.com/api/tasks/social/{user_id}", headers=headers)
            
            completed_tasks = []
            if user_tasks_response.status_code == 200:
                user_tasks_data = user_tasks_response.json()
                completed_tasks = [task.get('type') for task in user_tasks_data.get('data', [])]
            
            # Display available tasks and their status
            for i, task in enumerate(social_tasks):
                task_type = task.get('type')
                task_name = task.get('name', 'Unknown Task')
                point = task.get('point', 0)
                spin = task.get('spin', 0)
                
                status = "✅ Sudah diverifikasi" if task_type in completed_tasks else "❌ Belum diverifikasi"
                status_color = Fore.GREEN if task_type in completed_tasks else Fore.YELLOW
                            
            # Mark which tasks are completed
            for task in social_tasks:
                task['completed'] = task.get('type') in completed_tasks
            
            return social_tasks
        else:
            print(Fore.RED + f"Gagal mengambil data social tasks! Status code: {response.status_code}")
            return []
    except Exception as e:
        print(Fore.RED + f"Error saat mengambil social tasks: {str(e)}")
        return []

def load_verified_tasks():
    """Memuat data task yang sudah diverifikasi dari file JSON."""
    if not os.path.exists(VERIFIED_TASKS_FILE):
        return {}

    try:
        with open(VERIFIED_TASKS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(Fore.RED + "⚠️ File verified_tasks.json rusak, mengosongkan data.")
        return {}

def save_verified_tasks(verified_tasks):
    """Menyimpan data task yang sudah diverifikasi ke file JSON."""
    with open(VERIFIED_TASKS_FILE, "w") as f:
        json.dump(verified_tasks, f, indent=4)

def verify_task(user_id, token, task_type, point, spin, task_name="Unknown", username="Unknown"):
    try:
        # Load verified tasks
        verified_tasks = load_verified_tasks()
        
        # Cek apakah user sudah pernah verify task ini
        user_key = f"{username}_{user_id}"
        if user_key not in verified_tasks:
            verified_tasks[user_key] = []
            
        if task_type in verified_tasks[user_key]:
            print(Fore.YELLOW + f"ℹ️ Task '{task_name}' ({task_type}) sudah pernah diverifikasi sebelumnya oleh {username}")
            return True
            
        url = f"https://tgapi.zoop.com/api/tasks/verified/{user_id}"
        headers = create_header(token)
        payload = {"point": point, "spin": spin, "type": task_type}
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(Fore.GREEN + f"✅ Berhasil verifikasi task '{task_name}' ({task_type})")
            # Simpan ke daftar task yang terverifikasi
            verified_tasks[user_key].append(task_type)
            save_verified_tasks(verified_tasks)
            return True
        else:
            print(Fore.RED + f"❌ Gagal verifikasi task '{task_name}' ({task_type})! Status code: {response.status_code}")
            try:
                error_detail = response.json()
                if 'message' in error_detail:
                    # Jika pesan error menunjukkan sudah terverifikasi
                    if "already verified" in error_detail['message'].lower():
                        print(Fore.YELLOW + f"   Sepertinya task sudah pernah diverifikasi")
                        verified_tasks[user_key].append(task_type)
                        save_verified_tasks(verified_tasks)
                        return True
                    print(Fore.RED + f"   Pesan error: {error_detail['message']}")
            except:
                pass
                
            return False
    except Exception as e:
        print(Fore.RED + f"❌ Error saat verifikasi task '{task_name}' ({task_type}): {str(e)}")
        return False

def generate_random_name(length=5):
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    name = "".join(random.choice((consonants, vowels)[i % 2]) for i in range(length))
    return name.capitalize()

def register_zoop(user_id, token, username, emails):
    try:
        # Pastikan emails adalah list dan tidak kosong
        if not emails or not isinstance(emails, list):
            print(Fore.YELLOW + f"⚠️ Daftar email kosong atau tidak valid ({emails}), proses registrasi dilewati.")
            return False

        # Load email yang sudah digunakan
        used_emails = load_email_usage()

        # Cari email yang belum dipakai
        available_email = next((email for email in emails if email not in used_emails), None)

        # Jika tidak ada email yang tersisa, skip pendaftaran
        if not available_email:
            print(Fore.YELLOW + "⚠️ Semua email telah digunakan, proses registrasi dilewati untuk akun ini.")
            return False

        print(Fore.CYAN + f"📧 Menggunakan email: {available_email} untuk akun {username}")

        # Simpan email sebagai sudah digunakan SEBELUM mendaftar
        used_emails[available_email] = username
        save_email_usage(used_emails)

        url = f"https://tgapi.zoop.com/api/users/zoop/{user_id}"
        headers = create_header(token)

        payload = {
            "firstName": username.split('_')[0] if '_' in username else username,
            "lastName": generate_random_name(),
            "zoopEmail": available_email,
            "type": "REGISTER_ZOOP_APP"
        }

        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(Fore.GREEN + f"✅ Berhasil daftar ZOOP dengan email {available_email}")
            return True
        else:
            print(Fore.RED + f"❌ Gagal daftar ZOOP! Status code: {response.status_code}")

            # Jika gagal, hapus email dari daftar yang sudah digunakan
            del used_emails[available_email]
            save_email_usage(used_emails)

            return False
    except Exception as e:
        print(Fore.RED + f"❌ Error saat daftar ZOOP: {str(e)}")

        # Jika terjadi error, hapus email dari daftar yang sudah digunakan
        if available_email and available_email in used_emails:
            del used_emails[available_email]
            save_email_usage(used_emails)

        return False

def countdown_timer(end_time):
    while datetime.datetime.now() < end_time:
        remaining = end_time - datetime.datetime.now()
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown = f"{hours:02}:{minutes:02}:{seconds:02}"
        sys.stdout.write(f"\r{Fore.YELLOW}⏳ Menunggu reset: {countdown}")
        sys.stdout.flush()
        time.sleep(1)
    print("\n" + Fore.GREEN + "⏰ Waktu habis! Memulai kembali proses...")

def process_account(index, total, initData, emails=None):
    try:
        print(Fore.CYAN + f"\n[{index+1}/{total}] Memproses akun...")
        
        # Login
        token, info = login(initData)
        if not token or not info:
            print(Fore.RED + "❌ Gagal login, melanjutkan ke akun berikutnya...")
            return
        
        username = info.get('username', 'Unknown')
        user_id = info.get('userId', 0)
        point = info.get('point', 0)
        spin_count = info.get('spin', 0)
        
        print(Fore.CYAN + f"📱 Username: {username}")
        print(Fore.CYAN + f"🔑 User ID: {user_id}")
        print(Fore.CYAN + f"💎 Point: {point}")
        print(Fore.CYAN + f"🎡 Spin: {spin_count}")
        
        # Cek tasks
        tasks_data = check_tasks(user_id, token)
        if not tasks_data:
            print(Fore.RED + "❌ Gagal mendapatkan informasi tasks")
            return
        
        day_claimed = tasks_data.get('claimed', False)
        day_spined = tasks_data.get('spined', False)
        daily_index = tasks_data.get('dailyIndex', 1)
        
        # Claim daily reward jika belum
        if not day_claimed:
            claim_result = claim_daily_reward(user_id, token, daily_index)
            if claim_result:
                print(Fore.GREEN + f"✅ Berhasil claim reward harian (hari ke-{daily_index})")
        else:
            print(Fore.YELLOW + "ℹ️ Reward harian sudah diklaim")
        
        # Use all available spins
        if spin_count > 0:
            claim_spin(user_id, token, spin_count)
            # Mark daily spin if it wasn't marked yet
            if not day_spined:
                mark_daily_spin(user_id, token)
        else:
            print(Fore.YELLOW + "ℹ️ Tidak ada spin yang tersedia")
        
        # Ambil daftar task sosial
        social_tasks = get_social_tasks(token, user_id)
        if not social_tasks:
            print(Fore.RED + "❌ Gagal mendapatkan daftar social tasks")
            return
            
        # Load verified tasks untuk user ini
        verified_tasks = load_verified_tasks()
        user_key = f"{username}_{user_id}"
        if user_key not in verified_tasks:
            verified_tasks[user_key] = []
        
        # Display available tasks and their status
        print(Fore.CYAN + "\n📋 Daftar Task yang tersedia:")
        for i, task in enumerate(social_tasks):
            task_type = task.get('type')
            task_name = task.get('name', 'Unknown Task')
            point = task.get('point', 0)
            spin = task.get('spin', 0)
            
            is_verified = task_type in verified_tasks[user_key]
            status = "✅ Sudah diverifikasi" if is_verified else "❌ Belum diverifikasi"
            status_color = Fore.GREEN if is_verified else Fore.YELLOW
            
            print(f"{Fore.WHITE}{i+1}. {task_name}")
            print(f"   {Fore.MAGENTA}Type: {task_type}")
            print(f"   {Fore.GREEN}Reward: {point} points, {spin} spins")
            print(f"   {status_color}Status: {status}")
            
            # Add verification status to task object
            task['completed'] = is_verified
        
        # Verifikasi task yang belum diverifikasi
        for task in social_tasks:
            task_type = task.get('type')
            
            # Skip VERIFY_EMAIL task sesuai permintaan
            if task_type == "VERIFY_EMAIL":
                print(Fore.YELLOW + f"ℹ️ Melewati task 'VERIFY_EMAIL' (perlu verifikasi manual via email)")
                continue
                
            if not task.get('completed', False):
                task_name = task.get('name', 'Unknown Task')
                point = task.get('point', 0)
                spin = task.get('spin', 0)
                
                if task_type == "REGISTER_ZOOP_APP":
                    # Khusus untuk ZOOP registration, perlu cek tambahan
                    if not info.get('zoopSynced', False) and not info.get('emailVerified', False):
                        register_result = register_zoop(user_id, token, username, emails)
                        if register_result:
                            verify_task(user_id, token, task_type, point, spin, task_name, username)
                else:
                    # Untuk task lainnya, langsung verify
                    verify_task(user_id, token, task_type, point, spin, task_name, username)
        
        print(Fore.GREEN + f"✅ Proses untuk akun {username} selesai")
            
    except Exception as e:
        print(Fore.RED + f"Error saat memproses akun: {str(e)}")

def main():
    try:
        print_welcome_message()

        while True:
            accounts = load_accounts()
            emails = load_emails()  # Muat email sebelum memproses akun

            if not accounts:
                print(Fore.RED + "Tidak ada data akun yang ditemukan.")
                return
            
            total_accounts = len(accounts)
            print(Fore.CYAN + f"🔄 Total akun: {total_accounts}")

            for index, initData in enumerate(accounts):
                process_account(index, total_accounts, initData, emails)  # Kirim emails ke process_account

                # Jeda sebelum akun berikutnya
                if index < total_accounts - 1:
                    for i in range(5, 0, -1):
                        print(f"\r{Fore.YELLOW}⏳ Beralih ke akun berikutnya dalam {i} detik...", end="")
                        time.sleep(1)
                    print("\r" + " " * 50, end="\r")

            print(Fore.GREEN + "\n✅ Semua akun telah diproses!")

            # Hitung mundur 1 hari sebelum mulai ulang
            end_time = datetime.datetime.now() + datetime.timedelta(days=1)
            print(Fore.YELLOW + f"⏳ Menunggu sampai {end_time.strftime('%Y-%m-%d %H:%M:%S')} untuk memulai kembali...")
            countdown_timer(end_time)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️ Program dihentikan oleh pengguna.")
    except Exception as e:
        print(Fore.RED + f"\n❌ Error utama: {str(e)}")
        print(Fore.YELLOW + "⚠️ Mencoba memulai ulang program...")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
