from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
import requests
import base64
from dotenv import load_dotenv
from models import db, User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    app_url = os.getenv('APP_URL', 'http://localhost:5000')
    return render_template('index.html', app_url=app_url)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username sudah terdaftar', 'error')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Handle ganti tema (hanya untuk PRO)
    if request.method == 'POST' and current_user.is_pro:
        new_theme = request.form.get('theme_color')
        if new_theme in ['emerald', 'ruby', 'sapphire', 'gold']:
            user = User.query.get(current_user.id)
            user.theme_color = new_theme
            db.session.commit()
            flash("Tema berhasil diperbarui!", "success")
            return redirect(url_for('dashboard'))
    # Verifikasi pembayaran otomatis saat kembali ke dashboard (Berguna untuk Localhost tanpa Webhook)
    if not current_user.is_pro and 'last_invoice_id' in session:
        invoice_id = session['last_invoice_id']
        api_key = os.getenv('XENDIT_API_KEY')
        if api_key:
            auth_string = f"{api_key}:".encode('utf-8')
            base64_auth = base64.b64encode(auth_string).decode('utf-8')
            headers = {"Authorization": f"Basic {base64_auth}"}
            try:
                resp = requests.get(f"https://api.xendit.co/v2/invoices/{invoice_id}", headers=headers, timeout=5)
                if resp.status_code == 200:
                    status = resp.json().get('status')
                    if status in ['PAID', 'SETTLED']:
                        user = User.query.get(current_user.id)
                        user.is_pro = True
                        db.session.commit()
                        flash("Pembayaran berhasil dikonfirmasi dari Xendit! Anda sekarang adalah PRO.", "success")
                        session.pop('last_invoice_id', None)
            except:
                pass

    import datetime
    
    # Ambil data profile dari Chess.com Public API
    headers = {"User-Agent": "Chessfolio-CloudComputing-Project"}
    chess_data = {}
    rapid_rating = blitz_rating = puzzle_rating = 0
    pro_stats = None
    recent_games = []

    try:
        response = requests.get(f"https://api.chess.com/pub/player/{current_user.username}", headers=headers, timeout=15)
        if response.status_code == 200:
            chess_data = response.json()
            if 'joined' in chess_data:
                chess_data['joined_date'] = datetime.datetime.fromtimestamp(chess_data['joined']).strftime('%d %b %Y')
            if 'last_online' in chess_data:
                chess_data['online_date'] = datetime.datetime.fromtimestamp(chess_data['last_online']).strftime('%d %b %Y')
                
        # Ambil Basic Stats (Bisa dilihat semua user)
        stats_resp = requests.get(f"https://api.chess.com/pub/player/{current_user.username}/stats", headers=headers, timeout=15)
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            rapid_rating = stats.get('chess_rapid', {}).get('last', {}).get('rating', 0)
            blitz_rating = stats.get('chess_blitz', {}).get('last', {}).get('rating', 0)
            puzzle_rating = stats.get('tactics', {}).get('highest', {}).get('rating', 0)
            
            if current_user.is_pro:
                rapid_record = stats.get('chess_rapid', {}).get('record', {})
                pro_stats = {
                    'win': rapid_record.get('win', 0),
                    'loss': rapid_record.get('loss', 0),
                    'draw': rapid_record.get('draw', 0)
                }

        # Ambil Game History (Hanya untuk PRO)
        if current_user.is_pro:
            archives_resp = requests.get(f"https://api.chess.com/pub/player/{current_user.username}/games/archives", headers=headers, timeout=15)
            if archives_resp.status_code == 200:
                archives = archives_resp.json().get('archives', [])
                
                # Loop dari bulan terbaru ke belakang untuk mencari game
                all_recent_games = []
                for archive_url in reversed(archives):
                    games_resp = requests.get(archive_url, headers=headers, timeout=15)
                    if games_resp.status_code == 200:
                        month_games = games_resp.json().get('games', [])
                        if month_games:
                            all_recent_games.extend(reversed(month_games))
                            if len(all_recent_games) >= 5:
                                break
                
                # Format 5 game terakhir
                for g in all_recent_games[:5]:
                    g['end_date'] = datetime.datetime.fromtimestamp(g.get('end_time', 0)).strftime('%d %b %Y')
                recent_games = all_recent_games[:5]

    except Exception as e:
        print("Error fetching chess.com data:", e)
        
    return render_template('dashboard.html', 
                           chess_data=chess_data, 
                           rapid=rapid_rating, 
                           blitz=blitz_rating, 
                           puzzle=puzzle_rating,
                           pro_stats=pro_stats,
                           recent_games=recent_games)

@app.route('/admin')
@login_required
def admin():
    # Sederhana: anggap user dengan ID 1 adalah admin
    if current_user.id != 1:
        flash("Akses ditolak. Anda bukan admin.", "error")
        return redirect(url_for('dashboard'))
        
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/toggle_pro/<int:user_id>', methods=['POST'])
@login_required
def admin_toggle_pro(user_id):
    if current_user.id != 1:
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(user_id)
    user.is_pro = not user.is_pro
    db.session.commit()
    flash(f"Status PRO untuk {user.username} berhasil diubah.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.id != 1:
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(user_id)
    if user.id == 1:
        flash("Tidak bisa menghapus akun Admin Utama!", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} berhasil dihapus.", "success")
    return redirect(url_for('admin'))

@app.route('/checkout')
@login_required
def checkout():
    if current_user.is_pro:
        flash("Anda sudah berlangganan PRO!", "success")
        return redirect(url_for('dashboard'))
        
    api_key = os.getenv('XENDIT_API_KEY')
    if not api_key:
        flash("Sistem pembayaran sedang tidak tersedia.", "error")
        return redirect(url_for('dashboard'))
        
    # Xendit membutuhkan Basic Auth dengan format "api_key:" (di-encode base64)
    auth_string = f"{api_key}:".encode('utf-8')
    base64_auth = base64.b64encode(auth_string).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "external_id": f"chessfolio_pro_{current_user.id}_{os.urandom(4).hex()}",
        "amount": 15000,
        "payer_email": f"{current_user.username}@chessfolio.local",
        "description": "Upgrade ke Chessfolio PRO (Paket Menteri)",
        "success_redirect_url": url_for('dashboard', _external=True),
        "failure_redirect_url": url_for('pricing', _external=True),
        "currency": "IDR"
    }
    
    try:
        response = requests.post("https://api.xendit.co/v2/invoices", json=payload, headers=headers)
        if response.status_code == 200:
            invoice_data = response.json()
            session['last_invoice_id'] = invoice_data.get('id')
            return redirect(invoice_data.get('invoice_url'))
        else:
            flash("Gagal membuat tagihan. Silakan coba lagi.", "error")
            return redirect(url_for('pricing'))
    except Exception as e:
        flash("Terjadi kesalahan sistem.", "error")
        return redirect(url_for('pricing'))

@app.route('/webhook/xendit', methods=['POST'])
def xendit_webhook():
    data = request.json
    
    # Verifikasi Token Webhook Xendit
    xendit_callback_token = request.headers.get('x-callback-token')
    
    # (Di tahap produksi, cocokkan token ini dengan token dari Xendit Dashboard)
    # if xendit_callback_token != os.getenv('XENDIT_WEBHOOK_TOKEN'):
    #     return jsonify({"message": "Invalid token"}), 403
        
    if data and data.get('status') == 'PAID':
        external_id = data.get('external_id', '')
        # Format: chessfolio_pro_{user_id}_{random}
        parts = external_id.split('_')
        if len(parts) >= 3 and parts[0] == 'chessfolio' and parts[1] == 'pro':
            user_id = parts[2]
            user = User.query.get(int(user_id))
            if user:
                user.is_pro = True
                db.session.commit()
                print(f"[WEBHOOK] User {user.username} otomatis di-upgrade ke PRO!")
                
    return jsonify({"message": "Webhook received"}), 200

@app.route('/api/predict/<username>')
def api_predict(username):
    headers = {"User-Agent": "Chessfolio-CloudComputing-Project"}
    try:
        resp = requests.get(f"https://api.chess.com/pub/player/{username}/stats", headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            rapid_rating = data.get('chess_rapid', {}).get('last', {}).get('rating')
            if rapid_rating:
                return jsonify({"success": True, "rating": rapid_rating})
        return jsonify({"success": False, "message": "Pemain tidak ada atau belum punya rating Rapid"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": "Jaringan lambat / gagal koneksi ke Chess.com"}), 500

@app.route('/u/<username>')
def biolink(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if not user.is_pro:
        return "Biolink ini belum aktif atau pengguna bukan PRO.", 404
        
    headers = {"User-Agent": "Chessfolio-CloudComputing-Project"}
    try:
        response = requests.get(f"https://api.chess.com/pub/player/{user.username}", headers=headers, timeout=5)
        chess_data = response.json() if response.status_code == 200 else {}
        
        stats_resp = requests.get(f"https://api.chess.com/pub/player/{user.username}/stats", headers=headers, timeout=5)
        stats = stats_resp.json() if stats_resp.status_code == 200 else {}
        rapid_rating = stats.get('chess_rapid', {}).get('last', {}).get('rating', 0)
        
    except:
        chess_data = {}
        rapid_rating = 0
        
    return render_template('biolink.html', user=user, chess_data=chess_data, rapid_rating=rapid_rating)

# Helper to create DB tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
