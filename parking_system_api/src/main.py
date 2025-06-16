import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.usuarios import usuarios_bp
from src.routes.clientes import clientes_bp
from src.routes.veiculos import veiculos_bp
from src.routes.vagas import vagas_bp
from src.routes.estacionamentos import estacionamentos_bp
from src.routes.pagamentos import pagamentos_bp
from src.routes.relatorios import relatorios_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'parking_system_secret_key_2024'
app.config['JWT_SECRET_KEY'] = 'jwt_secret_key_parking_system_2024'

# Configuração CORS para permitir acesso do frontend
CORS(app, origins="*")

# Configuração JWT
jwt = JWTManager(app)

# Registro dos blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
app.register_blueprint(veiculos_bp, url_prefix='/api/veiculos')
app.register_blueprint(vagas_bp, url_prefix='/api/vagas')
app.register_blueprint(estacionamentos_bp, url_prefix='/api/estacionamentos')
app.register_blueprint(pagamentos_bp, url_prefix='/api/pagamentos')
app.register_blueprint(relatorios_bp, url_prefix='/api/relatorios')

# Configuração do banco de dados (SQLite para desenvolvimento)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
