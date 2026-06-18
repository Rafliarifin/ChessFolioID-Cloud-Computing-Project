import sys
import requests

def get_chess_profile(username):
    url = f"https://api.chess.com/pub/player/{username}"
    headers = {
        "User-Agent": "Chessfolio-CloudComputing-Project"
    }
    
    print(f"Mengambil data untuk username: {username}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("\nData berhasil ditemukan!")
            print("-" * 30)
            print(f"Username : {data.get('username', '-')}")
            print(f"Nama Asli: {data.get('name', 'Tidak dicantumkan')}")
            print(f"Followers: {data.get('followers', 0)}")
            print(f"Status   : {data.get('status', '-')}")
            print(f"Link     : {data.get('url', '-')}")
            print("-" * 30)
        else:
            print(f"Gagal mengambil data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Penggunaan: python cli_chess_api.py <username>")
        print("Contoh: python cli_chess_api.py hikaru")
    else:
        get_chess_profile(sys.argv[1])
