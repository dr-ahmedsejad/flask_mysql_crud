import base64
import os
import uuid
from flask import Flask, request, jsonify, url_for
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Permet les requêtes depuis des origines externes (nécessaire pour Flutter)

# Configuration de la base de données
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask_crud'

# Configuration pour le dossier d'upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

# Fonction pour vérifier si un fichier est autorisé
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API : Obtenir tous les items
@app.route('/api/items', methods=['GET'])
def get_items():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, description, image_path FROM items")
    items = cur.fetchall()
    cur.close()

    results = [
        {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'image': url_for('static', filename=row[3].replace('static/', ''), _external=True) if row[3] else None
        }
        for row in items
    ]

    return jsonify(results)

# API : Créer un nouvel item avec une image
@app.route('/api/create', methods=['POST'])
def api_create():
    try:
        # Vérifier si tous les champs requis sont présents
        data = request.get_json()
        if not data or 'name' not in data or 'description' not in data or 'image' not in data:
            return jsonify({'error': 'Champs obligatoires manquants'}), 400

        name = data['name']
        description = data['description']
        image_base64 = data['image']

        # Décoder l'image Base64
        try:
            image_data = base64.b64decode(image_base64)
        except Exception as e:
            return jsonify({'error': 'Image invalide ou non décodable'}), 400

        # Vérifier si le dossier d'upload existe, sinon le créer
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Générer un nom de fichier unique pour l'image
        unique_filename = f"{uuid.uuid4().hex}.jpg"  # Par défaut, l'image est enregistrée au format JPG
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename).replace("\\", "/")

        # Enregistrer l'image
        with open(image_path, 'wb') as image_file:
            image_file.write(image_data)

        # Chemin relatif pour la base de données
        relative_image_path = os.path.join('uploads', unique_filename).replace("\\", "/")

        # Insérer les données dans la base
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO items (name, description, image_path) VALUES (%s, %s, %s)",
            (name, description, relative_image_path)
        )
        mysql.connection.commit()
        return '', 201

    except Exception as e:
        print(f"Erreur : {e}")
        return jsonify({'error': str(e)}), 500

# API : Mettre à jour un item
@app.route('/api/update/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        # Lire les données JSON envoyées par le client
        data = request.get_json()

        # Vérifier si les champs requis sont présents
        if not data or 'name' not in data or 'description' not in data:
            return jsonify({'error': 'Champs obligatoires manquants'}), 400

        name = data['name']
        description = data['description']
        image_path = None

        # Gérer l'image encodée en Base64 si présente
        if 'image' in data:
            try:
                # Décoder l'image Base64
                image_data = base64.b64decode(data['image'])
                unique_filename = f"{uuid.uuid4().hex}.jpg"  # Nom unique avec extension JPG
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename).replace("\\", "/")

                # Enregistrer l'image
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                with open(image_path, 'wb') as image_file:
                    image_file.write(image_data)

                # Chemin relatif pour la base de données
                relative_image_path = os.path.join('uploads', unique_filename).replace("\\", "/")
            except Exception as e:
                return jsonify({'error': 'Erreur lors du traitement de l\'image'}), 400

        # Mise à jour dans la base de données
        cur = mysql.connection.cursor()
        if image_path:
            cur.execute(
                "UPDATE items SET name = %s, description = %s, image_path = %s WHERE id = %s",
                (name, description, relative_image_path, item_id)
            )
        mysql.connection.commit()

        return '', 200

    except Exception as e:
        print(f"Erreur : {e}")
        return jsonify({'error': str(e)}), 500




# API : Supprimer un item
@app.route('/api/delete/<int:id>', methods=['DELETE'])
def api_delete(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM items WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        print(f"Erreur : {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True)
