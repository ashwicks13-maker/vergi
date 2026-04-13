from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.json.ensure_ascii = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vergi.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_query(query, params=()):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

# En ilkel ama en garantici temizlik
def clean_sql(column):
    return f"REPLACE(REPLACE(REPLACE({column}, char(10), ''), char(13), ''), '''', '')"

@app.route("/vergi-adi")
def vergi_adi():
    ad = request.args.get("adi", "").strip()
    soyad = request.args.get("soyadi", "").strip()

    if not ad and not soyad:
        return jsonify({"hata": "Ad veya soyad giriniz"}), 400

    # Karakter eşleşme sorununu aşmak için 
    # hem küçük hem büyük harf varyasyonlarını deniyoruz
    term1 = f"%{ad.lower()}%"
    term2 = f"%{ad.upper()}%"
    term3 = f"%{ad.capitalize()}%"
    
    # Soyad varsa onun için de varyasyonlar
    s_term1 = f"%{soyad.lower()}%" if soyad else None

    if ad and soyad:
        # Hem ad hem soyad varyasyonlarını içeren geniş sorgu
        sql = f"""SELECT * FROM kisiler WHERE 
                  ({clean_sql('fullname')} LIKE ? OR {clean_sql('fullname')} LIKE ?) AND 
                  ({clean_sql('fullname')} LIKE ?) LIMIT 50"""
        params = (term1, term2, s_term1)
    else:
        aranan = ad if ad else soyad
        sql = f"SELECT * FROM kisiler WHERE {clean_sql('fullname')} LIKE ? OR {clean_sql('fullname')} LIKE ? LIMIT 50"
        params = (f"%{aranan.lower()}%", f"%{aranan.upper()}%")

    sonuc = db_query(sql, params)
    return jsonify({"status": "success", "count": len(sonuc), "data": sonuc})

@app.route("/vergi-tc")
def vergi_tc():
    tc = request.args.get("tc", "").strip()
    # TC'de tırnak varsa temizle
    sql = f"SELECT * FROM kisiler WHERE {clean_sql('identity')} LIKE ? LIMIT 1"
    sonuc = db_query(sql, (f"%{tc}%",))
    return jsonify({"status": "success", "count": len(sonuc), "data": sonuc})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
