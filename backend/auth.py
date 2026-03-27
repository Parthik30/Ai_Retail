from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

from backend.db import SessionLocal
from backend.models import User


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'), static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'))
app.secret_key = os.getenv('FLASK_SECRET', 'dev-secret')


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username')
        password = request.form.get('password')

        db = SessionLocal()
        try:
            user = db.query(User).filter((User.username == identifier) | (User.email == identifier)).first()
        finally:
            db.close()

        # NOTE: current project stores password_hash as plain text in seed. Compare directly.
        if user and user.password_hash == password:
            session['user_id'] = user.user_id
            session['username'] = user.username
            return redirect(url_for('dashboard'))

        flash('Invalid credentials')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', '5000')))
