from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from src.models.database import db, Usuario, HistoricoAtividade
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticação de usuários"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
        
        usuario = Usuario.query.filter_by(email=data['email']).first()
        
        if not usuario or not check_password_hash(usuario.senha_hash, data['senha']):
            return jsonify({'erro': 'Credenciais inválidas'}), 401
        
        if not usuario.ativo:
            return jsonify({'erro': 'Usuário inativo'}), 401
        
        # Criar token JWT
        access_token = create_access_token(
            identity=usuario.id,
            expires_delta=timedelta(hours=8)
        )
        
        # Registrar atividade
        atividade = HistoricoAtividade(
            usuario_id=usuario.id,
            acao='login',
            detalhes=f'Login realizado por {usuario.email}'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({
            'token': access_token,
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Endpoint para obter informações do usuário atual"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Endpoint para logout (registra atividade)"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if usuario:
            # Registrar atividade
            atividade = HistoricoAtividade(
                usuario_id=usuario.id,
                acao='logout',
                detalhes=f'Logout realizado por {usuario.email}'
            )
            db.session.add(atividade)
            db.session.commit()
        
        return jsonify({'mensagem': 'Logout realizado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

