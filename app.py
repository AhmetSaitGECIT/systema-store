import sqlite3
import datetime
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'systema_ultra_secure_key'
app.permanent_session_lifetime = timedelta(days=30) 

def get_db():
    conn = sqlite3.connect('systema_final_v5.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Ürünler
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, old_price REAL, 
                  image TEXT, category TEXT, link TEXT, installment TEXT, 
                  is_follower INTEGER DEFAULT 0, created_at TIMESTAMP)''')
    # Haberler
    c.execute('''CREATE TABLE IF NOT EXISTS news 
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, date TEXT)''')
    # İstekler
    c.execute('''CREATE TABLE IF NOT EXISTS requests 
                 (id INTEGER PRIMARY KEY, username TEXT, message TEXT, date TEXT)''')
    # Reklamlar
    c.execute('''CREATE TABLE IF NOT EXISTS ads 
                 (id INTEGER PRIMARY KEY, image TEXT, link TEXT)''')
    # KATEGORİLER (YENİ)
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY, name TEXT)''')
    
    # EĞER KATEGORİ YOKSA SENİN LİSTENİ OTOMATİK EKLE
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = ["Oyun / Key", "Hazır Sistem", "Laptop", "Playstation", "Xbox", 
                        "Monitör", "Ekran Kartı", "İşlemci", "Ram", "Anakart", 
                        "Mouse", "Klavye", "Kulaklık", "Kulaklık Standı", 
                        "Mousepad", "Fan", "Kasa", "Mikrofon", "Koltuk"]
        for cat in default_cats:
            c.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        conn.commit()

    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = get_db()
    limit = datetime.datetime.now() - datetime.timedelta(hours=24)
    conn.execute("DELETE FROM products WHERE created_at < ?", (limit,))
    conn.commit()
    
    # FİLTRELEME & SIRALAMA
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

    products = conn.execute(query, params).fetchall()
    news = conn.execute("SELECT * FROM news ORDER BY id DESC LIMIT 5").fetchall()
    ad = conn.execute("SELECT * FROM ads ORDER BY id DESC LIMIT 1").fetchone()
    # Kategorileri çek
    categories = conn.execute("SELECT * FROM categories").fetchall()
    
    conn.close()
    return render_template('index.html', products=products, news=news, ad=ad, categories=categories)

@app.route('/submit-request', methods=['POST'])
def submit_request():
    user = request.form['username']
    msg = request.form['message']
    conn = get_db()
    conn.execute("INSERT INTO requests (username, message, date) VALUES (?,?,?)", 
                 (user, msg, datetime.datetime.now().strftime("%d.%m.%Y")))
    conn.commit()
    conn.close()
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
        # ÜRÜN EKLE
        if 'add_product' in request.form:
            name = request.form['name']
            price = request.form['price']
            img = request.form['image']
            cat = request.form['category']
            link = request.form['link']
            is_follower = 1 if 'is_follower' in request.form else 0
            conn.execute("INSERT INTO products (name, price, old_price, image, category, link, installment, is_follower, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                         (name, price, float(price)*1.2, img, cat, link, "Fırsat Ürünü", is_follower, datetime.datetime.now()))
            conn.commit()
        # HABER EKLE
        elif 'add_news' in request.form:
            conn.execute("INSERT INTO news (title, content, date) VALUES (?,?,?)",
                         (request.form['title'], request.form['content'], datetime.datetime.now().strftime("%d.%m")))
            conn.commit()
        # REKLAM EKLE
        elif 'add_ad' in request.form:
            conn.execute("INSERT INTO ads (image, link) VALUES (?,?)", (request.form['image'], request.form['link']))
            conn.commit()
        # KATEGORİ EKLE (YENİ)
        elif 'add_cat' in request.form:
            conn.execute("INSERT INTO categories (name) VALUES (?)", (request.form['cat_name'],))
            conn.commit()
        
        # SİLME İŞLEMLERİ
        elif 'delete' in request.form:
            conn.execute("DELETE FROM products WHERE id = ?", (request.form['id'],))
            conn.commit()
        elif 'delete_req' in request.form:
            conn.execute("DELETE FROM requests WHERE id = ?", (request.form['req_id'],))
            conn.commit()
        elif 'delete_news' in request.form:
            conn.execute("DELETE FROM news WHERE id = ?", (request.form['news_id'],))
            conn.commit()
        elif 'delete_ad' in request.form:
            conn.execute("DELETE FROM ads WHERE id = ?", (request.form['ad_id'],))
            conn.commit()
        elif 'delete_cat' in request.form:
            conn.execute("DELETE FROM categories WHERE id = ?", (request.form['cat_id'],))
            conn.commit()

    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    reqs = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
    news_list = conn.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    active_ad = conn.execute("SELECT * FROM ads ORDER BY id DESC LIMIT 1").fetchone()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    
    conn.close()
    return render_template('admin.html', products=products, reqs=reqs, news_list=news_list, active_ad=active_ad, categories=categories)

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
    init_db()
    app.run(debug=True)