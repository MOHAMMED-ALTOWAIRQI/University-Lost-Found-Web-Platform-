from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from database import db_connect

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db_connect()
        c = conn.cursor(dictionary=True)

        c.execute("SELECT * FROM users WHERE username=%s", (username,))
        if c.fetchone():
            flash("Username already exists")
            conn.close()
            return redirect(url_for('signup.signup'))

        password_hash = generate_password_hash(password)
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()

        session['user_id'] = c.lastrowid
        session['username'] = username
        conn.close()

        return redirect(url_for('select_role'))

    return render_template('signup.html')
