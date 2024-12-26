import os

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Autorise toutes les origines

# Configuration de la base de données
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask_crud'

mysql = MySQL(app)

# Configuration pour le téléchargement des fichiers
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fonction pour vérifier les extensions de fichier
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route : Liste des items
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    cur.close()
    return render_template('index.html', items=items)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        file = request.files['image']

        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"{UPLOAD_FOLDER}/{filename}"

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO items (name, description, image_path) VALUES (%s, %s, %s)",
                    (name, description, image_path))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    return render_template('create.html')

# Route : Mettre à jour un item
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        file = request.files['image']

        # Gérer le téléchargement de l'image si elle est fournie
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"{UPLOAD_FOLDER}/{filename}"
            # Mettre à jour avec une nouvelle image
            cur.execute("UPDATE items SET name = %s, description = %s, image_path = %s WHERE id = %s",
                        (name, description, image_path, id))
        else:
            # Mettre à jour sans changer l'image
            cur.execute("UPDATE items SET name = %s, description = %s WHERE id = %s",
                        (name, description, id))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    # Récupérer les données actuelles de l'item
    cur.execute("SELECT id, name, description, image_path FROM items WHERE id = %s", (id,))
    item = cur.fetchone()
    cur.close()

    return render_template('update.html', item=item)


# Route : Supprimer un item
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM items WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))


app.run(host='0.0.0.0', port=5000)

