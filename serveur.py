from flask import request, redirect, url_for, Flask, render_template, jsonify
from flask_mail import Mail, Message  # Pour l'envoi d'emails
import serial
import time
import sqlite3
import os
import smtplib

# Configuration des répertoires
project_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(project_dir, '', 'html')

app = Flask(__name__, static_folder='static', template_folder=template_dir)

# Configuration du port série pour le HC-06 (modifier selon ton PC)
SERIAL_PORT = 'COM2'  # Modifier selon le port utilisé sous Windows
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except Exception as e:
    print("Erreur de connexion au HC-06:", e)
    ser = None

# Création et initialisation de la base de données
def eolien_db():
    conn = sqlite3.connect("vent.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vent_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            value REAL
        )
    """)
    conn.commit()
    conn.close()

eolien_db()

# Lecture des données du HC-06 et stockage dans la base
def lecture_HC06():
    if ser is not None and ser.in_waiting > 0:
        vent = ser.readline().decode('utf-8').strip()
        try:
            value = float(vent)  # Supposons que le HC-06 envoie une valeur numérique
            conn = sqlite3.connect("vent.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO vent_data (value) VALUES (?)", (value,))
            conn.commit()
            conn.close()
            return value
        except ValueError:
            print("Donnée invalide reçue :", vent)
    return None

# Configuration du serveur SMTP pour l'envoi d'emails (Outlook)
app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Serveur SMTP Outlook
app.config['MAIL_PORT'] = 587  # Port sécurisé
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Récupéré depuis une variable d'environnement
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Mot de passe sécurisé
app.config['MAIL_USE_TLS'] = True  # Utilisation de TLS
app.config['MAIL_USE_SSL'] = False  # Désactiver SSL

# Création d'une instance de Flask-Mail
mail = Mail(app)

# Récupération des données pour le site web
@app.route('/vent')
def get_vent():
    lecture_HC06()  # Lecture des données du HC-06 et stockage dans la base
    conn = sqlite3.connect("vent.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, value FROM vent_data ORDER BY id DESC LIMIT 10")
    vent = cursor.fetchall()
    conn.close()
    return jsonify(vent)

# Page web principale
@app.route('/')
def index():
    return render_template("accueil.html")

# Page Contact
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message_content = request.form['message']

        try:
            msg = Message(
                subject='Nouveau message de contact',
                sender=app.config['MAIL_USERNAME'],
                recipients=['sammoh974@outlook.fr']  # Remplace par ton adresse
            )
            msg.body = f"Nom: {name}\nEmail: {email}\nMessage:\n{message_content}"
            mail.send(msg)
            print("E-mail envoyé avec succès !")
        except Exception as e:
            print("Erreur lors de l'envoi de l'email :", e)
            return f"Erreur lors de l'envoi de l'email : {e}"
        return redirect(url_for('index'))

    return render_template("contact.html")

# Page Réalisation
@app.route('/realisation')
def realisation():
    return render_template("realisation.html")

# Page Services
@app.route('/services')
def services():
    return render_template("services.html")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
