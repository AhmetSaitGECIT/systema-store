import sqlite3
import datetime
import os
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'systema_ultra_secure_key'
app.permanent_session_lifetime = timedelta(days=30) 

# --- VERİTABANI YOLUNU GARANTİYE ALMA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'systema_final_v5.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Tablolar
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, old_price REAL, 
                  image TEXT, category TEXT, link TEXT, installment TEXT, 
                  is_follower INTEGER DEFAULT 0, created_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS news 
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS requests 
                 (id INTEGER PRIMARY KEY, username TEXT, message TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ads 
                 (id INTEGER PRIMARY KEY, image TEXT, link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY, name TEXT)''')
    # YENİ TABLO: TAVSİYELER
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations 
                 (id INTEGER PRIMARY KEY, username TEXT, title TEXT, price REAL, link TEXT, date TEXT)''')
    
    # Varsayılan kategoriler
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = ["Oyun / Key", "Hazır Sistem", "Laptop", "Playstation", "Xbox", 
                        "Monitör", "Ekran Kartı", "İşlemci", "Ram", "Anakart", 
                        "Mouse", "Klavye", "Kulaklık", "Kulaklık Standı", 
                        "Mousepad", "Fan", "Kasa", "Mikrofon", "Koltuk", "Takipçi Tavsiyesi"]
        for cat in default_cats:
            c.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        conn.commit()

    conn.commit()
    conn.close()

# Otomatik Başlatma
with app.app_context():
    init_db()

@app.route('/')
def home():
    conn = get_db()
    # 24 Saat Temizliği
    try:
        limit = datetime.datetime.now() - datetime.timedelta(hours=24)
        conn.execute("DELETE FROM products WHERE created_at < ?", (limit,))
        conn.commit()
    except:
        pass # Hata verirse geç (Site çökmesin)
    
    sort_by = request.args.get('sort', 'default')
    min_price = request.args.get('min')
    max_price = request.args.get('max')
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if min_price and min_price.isdigit():
        query += " AND price >= ?"
        params.append(int(min_price))
    if max_price and max_price.isdigit():
        query += " AND price <= ?"
        params.append(int(max_price))
        
    if sort_by == 'asc': query += " ORDER BY price ASC"
    elif sort_by == 'desc': query += " ORDER BY price DESC"
    else: query += " ORDER BY is_follower DESC, id DESC"

    try:
        products = conn.execute(query, params).fetchall()
        news = conn.execute("SELECT * FROM news ORDER BY id DESC LIMIT 5").fetchall()
        ad = conn.execute("SELECT * FROM ads ORDER BY id DESC LIMIT 1").fetchone()
        categories = conn.execute("SELECT * FROM categories").fetchall()
    except:
        products, news, ad, categories = [], [], None, []

    conn.close()
    return render_template('index.html', products=products, news=news, ad=ad, categories=categories)

# --- TAVSİYE GÖNDERME ---
@app.route('/submit-recommendation', methods=['POST'])
def submit_recommendation():
    try:
        user = request.form['username']
        title = request.form['title']
        price = request.form['price']
        link = request.form['link']
        
        conn = get_db()
        conn.execute("INSERT INTO recommendations (username, title, price, link, date) VALUES (?,?,?,?,?)", 
                     (user, title, price, link, datetime.datetime.now().strftime("%d.%m.%Y")))
        conn.commit()
        conn.close()
    except:
        pass # Hata olursa ana sayfaya dön
    return redirect(url_for('home'))

@app.route('/submit-request', methods=['POST'])
def submit_request():
    try:
        user = request.form['username']
        msg = request.form['message']
        conn = get_db()
        conn.execute("INSERT INTO requests (username, message, date) VALUES (?,?,?)", 
                     (user, msg, datetime.datetime.now().strftime("%d.%m.%Y")))
        conn.commit()
        conn.close()
    except:
        pass
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == "ahmetsaitnt" and request.form['password'] == "AserLostY_T3":
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    
    if request.method == 'POST':
        try:
            if 'add_product' in request.form:
                name = request.form['name']
                price = request.form['price']
                old_price = request.form['old_price']
                img = request.form['image']
                cat = request.form['category']
                link = request.form['link']
                is_follower = 1 if 'is_follower' in request.form else 0
                
                conn.execute("INSERT INTO products (name, price, old_price, image, category, link, installment, is_follower, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                             (name, price, old_price, img, cat, link, "Fırsat Ürünü", is_follower, datetime.datetime.now()))
                conn.commit()
            
            # TAVSİYE ONAYLA
            elif 'approve_rec' in request.form:
                rec_id = request.form['rec_id']
                rec = conn.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,)).fetchone()
                if rec:
                    default_img = "https://cdn-icons-png.flaticon.com/512/3081/3081329.png"
                    # old_price yerine normal fiyatı koyuyoruz ki indirim yokmuş gibi görünsün
                    conn.execute("INSERT INTO products (name, price, old_price, image, category, link, installment, is_follower, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                 (f"{rec['username']} Tavsiyesi: {rec['title']}", rec['price'], rec['price'], default_img, "Takipçi Tavsiyesi", rec['link'], "Takipçi Seçimi", 1, datetime.datetime.now()))
                    conn.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,)).commit()

            elif 'delete_rec' in request.form:
                conn.execute("DELETE FROM recommendations WHERE id = ?", (request.form['rec_id'],)).commit()

            elif 'add_news' in request.form:
                conn.execute("INSERT INTO news (title, content, date) VALUES (?,?,?)",
                             (request.form['title'], request.form['content'], datetime.datetime.now().strftime("%d.%m"))).commit()
            elif 'add_ad' in request.form:
                conn.execute("INSERT INTO ads (image, link) VALUES (?,?)", (request.form['image'], request.form['link'])).commit()
            elif 'add_cat' in request.form:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (request.form['cat_name'],)).commit()
            elif 'delete' in request.form:
                conn.execute("DELETE FROM products WHERE id = ?", (request.form['id'],)).commit()
            elif 'delete_req' in request.form:
                conn.execute("DELETE FROM requests WHERE id = ?", (request.form['req_id'],)).commit()
            elif 'delete_news' in request.form:
                conn.execute("DELETE FROM news WHERE id = ?", (request.form['news_id'],)).commit()
            elif 'delete_ad' in request.form:
                conn.execute("DELETE FROM ads WHERE id = ?", (request.form['ad_id'],)).commit()
            elif 'delete_cat' in request.form:
                conn.execute("DELETE FROM categories WHERE id = ?", (request.form['cat_id'],)).commit()
        except Exception as e:
            print("HATA:", e) # Loglara hatayı basar

    try:
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        reqs = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
        news_list = conn.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
        active_ad = conn.execute("SELECT * FROM ads ORDER BY id DESC LIMIT 1").fetchone()
        categories = conn.execute("SELECT * FROM categories").fetchall()
        
        # Tavsiyeler tablosu yoksa boş liste döndür (Hata vermesin)
        try:
            recommendations = conn.execute("SELECT * FROM recommendations ORDER BY id DESC").fetchall()
        except:
            recommendations = []
            
    except:
        products, reqs, news_list, active_ad, categories, recommendations = [], [], [], None, [], []
    
    conn.close()
    return render_template('admin.html', products=products, reqs=reqs, news_list=news_list, active_ad=active_ad, categories=categories, recommendations=recommendations)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute("UPDATE products SET name=?, price=?, image=?, link=? WHERE id=?",
                     (request.form['name'], request.form['price'], request.form['image'], request.form['link'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('edit.html', p=product)

if __name__ == '__main__':
    app.run(debug=True)
