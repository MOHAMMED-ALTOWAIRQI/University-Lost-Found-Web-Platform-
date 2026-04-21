from flask import Flask, render_template, redirect, url_for, session, request, flash
from database import db_connect
from login import login_bp
from signup import signup_bp
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret_here"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(login_bp)
app.register_blueprint(signup_bp)

@app.route("/")
def home():
    session.clear()
    return redirect(url_for("login.login"))

@app.route('/select_role', methods=['GET', 'POST'])
def select_role():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    if request.method == 'POST':
        session['role'] = request.form['role']
        return redirect(url_for('items'))

    return render_template('role_select.html', username=session.get('username'))

@app.route('/owner')
def owner():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    session['role'] = 'owner'
    return render_template('owner.html')

@app.route('/finder')
def finder():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    session['role'] = 'finder'
    return render_template('finder.html')

@app.route('/items')
def items():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()

    return render_template('items.html', items=items)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    if session.get('role') != 'finder':
        flash("Only finders can add found items.", "danger")
        return redirect(url_for('items'))

    if request.method == 'POST':
        conn = db_connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (user_id, item_type, item_name, category, description, location)
            VALUES (%s, 'found', %s, %s, %s, %s)
        """, (
            session['user_id'],
            request.form['item_name'],
            request.form['category'],
            request.form['description'],
            request.form['location']
        ))
        conn.commit()
        conn.close()

        flash("Item added successfully.", "success")
        return redirect(url_for('items'))

    return render_template('add_item.html')

@app.route('/claim/<int:item_id>', methods=['GET', 'POST'])
def claim_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM items WHERE item_id=%s", (item_id,))
    item = c.fetchone()

    if not item:
        conn.close()
        flash("Item not found.", "danger")
        return redirect(url_for('items'))

    if item['user_id'] == session['user_id']:
        conn.close()
        flash("You cannot claim your own item.", "danger")
        return redirect(url_for('items'))

    if request.method == 'POST':
        c.execute("""
            INSERT INTO claims (item_id, claimant_id, secret_detail_provided)
            VALUES (%s, %s, %s)
        """, (item_id, session['user_id'], request.form['secret_answer']))
        conn.commit()
        conn.close()

        flash("Claim sent successfully.", "success")
        return redirect(url_for('items'))

    conn.close()
    return render_template('claim.html', item=item)

@app.route('/approve_claim/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)

    c.execute("""
        SELECT c.*, i.user_id AS finder_id
        FROM claims c
        JOIN items i ON c.item_id = i.item_id
        WHERE c.claim_id=%s
    """, (claim_id,))
    claim = c.fetchone()

    if not claim or claim['finder_id'] != session['user_id']:
        conn.close()
        flash("Unauthorized action.", "danger")
        return redirect(url_for('items'))

    c.execute("UPDATE claims SET claim_status='approved' WHERE claim_id=%s", (claim_id,))
    c.execute("""
        INSERT INTO chats (item_id, claim_id, owner_id, finder_id)
        VALUES (%s, %s, %s, %s)
    """, (claim['item_id'], claim_id, claim['claimant_id'], session['user_id']))

    chat_id = c.lastrowid
    conn.commit()
    conn.close()

    return redirect(url_for('chat', chat_id=chat_id))
@app.route('/finder/claims')
def finder_claims():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)

    c.execute("""
        SELECT c.claim_id, i.item_name, u.username AS claimant
        FROM claims c
        JOIN items i ON c.item_id = i.item_id
        JOIN users u ON c.claimant_id = u.user_id
        WHERE i.user_id = %s
    """, (session['user_id'],))

    claims = c.fetchall()
    conn.close()

    return render_template('finder_claims.html', claims=claims)

@app.route('/chat/<int:chat_id>', methods=['GET', 'POST'])
def chat(chat_id):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)

    c.execute("""
        SELECT * FROM chats
        WHERE chat_id=%s AND (owner_id=%s OR finder_id=%s)
    """, (chat_id, session['user_id'], session['user_id']))
    chat = c.fetchone()

    if not chat:
        conn.close()
        flash("Unauthorized access.", "danger")
        return redirect(url_for('items'))

    if request.method == 'POST':
        msg = request.form.get('message')
        img = request.files.get('image')
        img_path = None

        if img and img.filename:
            filename = secure_filename(img.filename)
            img_path = f"{chat_id}_{filename}"
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_path))

        if msg or img_path:
            c.execute("""
                INSERT INTO messages (chat_id, sender_id, message, image_path)
                VALUES (%s, %s, %s, %s)
            """, (chat_id, session['user_id'], msg, img_path))
            conn.commit()

        return redirect(url_for('chat', chat_id=chat_id))

    c.execute("""
        SELECT * FROM messages
        WHERE chat_id=%s ORDER BY created_at
    """, (chat_id,))
    messages = c.fetchall()

    conn.close()
    return render_template('chat.html', messages=messages, chat_id=chat_id)

@app.route('/chats')
def my_chats():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)

    c.execute("""
        SELECT ch.chat_id, i.item_name, u.username AS other_user
        FROM chats ch
        JOIN items i ON ch.item_id = i.item_id
        JOIN users u 
            ON (CASE 
                    WHEN ch.owner_id = %s THEN ch.finder_id 
                    ELSE ch.owner_id 
                END) = u.user_id
        WHERE ch.owner_id = %s OR ch.finder_id = %s
        ORDER BY ch.created_at DESC
    """, (session['user_id'], session['user_id'], session['user_id']))

    chats = c.fetchall()
    conn.close()

    return render_template('my_chats.html', chats=chats)
@app.route('/close_chat/<int:chat_id>', methods=['POST'])
def close_chat(chat_id):
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    conn = db_connect()
    c = conn.cursor(dictionary=True)

    c.execute("""
        SELECT * FROM chats
        WHERE chat_id=%s AND (owner_id=%s OR finder_id=%s)
    """, (chat_id, session['user_id'], session['user_id']))
    chat = c.fetchone()
    conn.close()

    if not chat:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('items'))

    item_id = chat['item_id']

    conn = db_connect()
    c = conn.cursor()

    c.execute("""
        DELETE m FROM messages m
        JOIN chats ch ON m.chat_id = ch.chat_id
        WHERE ch.item_id = %s
    """, (item_id,))

    c.execute("DELETE FROM chats WHERE item_id = %s", (item_id,))

    c.execute("DELETE FROM claims WHERE item_id = %s", (item_id,))

    c.execute("DELETE FROM items WHERE item_id = %s", (item_id,))

    conn.commit()
    conn.close()

    flash("Agreement completed successfully.", "success")
    return redirect(url_for('items'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))

if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")
