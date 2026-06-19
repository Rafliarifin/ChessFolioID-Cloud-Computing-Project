import requests
import sys

def simulate_payment(user_id):
    print(f"🔄 Mengirim simulasi Webhook Xendit untuk User ID: {user_id}...")
    
    # Payload palsu seolah-olah dari Xendit
    data = {
        "status": "PAID",
        "external_id": f"chessfolio_pro_{user_id}_simulasi123"
    }
    
    try:
        response = requests.post("http://127.0.0.1:5000/webhook/xendit", json=data)
        if response.status_code == 200:
            print("✅ BERHASIL! Xendit Webhook sukses diterima server.")
            print(f"👉 Silakan cek halaman Dashboard, User ID {user_id} seharusnya sudah menjadi PRO sekarang!")
        else:
            print(f"❌ Gagal mengirim webhook. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: Pastikan server flask (app.py) sedang berjalan. Detail: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    else:
        # Default ke user ID 2 (asumsi user pertama yang daftar setelah admin)
        target_id = "2"
        
    simulate_payment(target_id)
