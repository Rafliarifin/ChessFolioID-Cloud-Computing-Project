from flask import Flask, render_template
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key')

@app.route('/')
def home():
    # Mengirimkan URL dari environment ke template
    app_url = os.getenv('APP_URL', 'http://localhost:5000')
    return render_template('index.html', app_url=app_url)

if __name__ == '__main__':
    # Mode debug akan otomatis aktif jika diatur di .env (FLASK_DEBUG=1)
    app.run(host='0.0.0.0', port=5000)
