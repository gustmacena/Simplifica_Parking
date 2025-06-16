from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from src.models.database import db, Usuario, HistoricoAtividade

usuarios_bp = Blueprint('usuarios', __name__)

def verificar_permissao_admin():
    """Verifica se o usuário atual é administrador"""
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    return usuario and usuario.nivel_acesso == 'admin'

@usuarios_bp.route('/', methods=['GET'])
@jwt_required()
def listar_usuarios():
    """Lista todos os usuários (apenas admins)"""
    try:
        if not verificar_permissao_admin():
            return jsonify({'erro': 'Acesso negado'}), 403
        
        usuarios = Usuario.query.all()
        return jsonify([usuario.to_dict() for usuario in usuarios]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@usuarios_bp.route('/', methods=['POST'])
@jwt_required()
def criar_usuario():
    """Cria um novo usuário (apenas admins)"""
    try:
        if not verificar_permissao_admin():
            return jsonify({'erro': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validações
        campos_obrigatorios = ['nome', 'email', 'senha', 'nivel_acesso']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'{campo} é obrigatório'}), 400
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'erro': 'Email já cadastrado'}), 400
        
        # Criar usuário
        usuario = Usuario(
            nome=data['nome'],
            email=data['email'],
            senha_hash=generate_password_hash(data['senha']),
            nivel_acesso=data['nivel_acesso'],
            ativo=data.get('ativo', True)
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        # Registrar atividade
        usuario_atual_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_atual_id,
            acao='criar_usuario',
            detalhes=f'Usuário {usuario.email} criado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@usuarios_bp.route('/<usuario_id>', methods=['GET'])
@jwt_required()
def obter_usuario(usuario_id):
    """Obtém um usuário específico"""
    try:
        usuario_atual_id = get_jwt_identity()
        usuario_atual = Usuario.query.get(usuario_atual_id)
        
        # Usuário pode ver seus próprios dados ou admin pode ver qualquer um
        if usuario_atual_id != usuario_id and usuario_atual.nivel_acesso != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@usuarios_bp.route('/<usuario_id>', methods=['PUT'])
@jwt_required()
def atualizar_usuario(usuario_id):
    """Atualiza um usuário"""
    try:
        usuario_atual_id = get_jwt_identity()
        usuario_atual = Usuario.query.get(usuario_atual_id)
        
        # Usuário pode atualizar seus próprios dados ou admin pode atualizar qualquer um
        if usuario_atual_id != usuario_id and usuario_atual.nivel_acesso != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'nome' in data:
            usuario.nome = data['nome']
        if 'email' in data:
            # Verificar se email já existe (exceto o próprio usuário)
            email_existente = Usuario.query.filter_by(email=data['email']).first()
            if email_existente and email_existente.id != usuario_id:
                return jsonify({'erro': 'Email já cadastrado'}), 400
            usuario.email = data['email']
        if 'senha' in data:
            usuario.senha_hash = generate_password_hash(data['senha'])
        
        # Apenas admin pode alterar nível de acesso e status ativo
        if usuario_atual.nivel_acesso == 'admin':
            if 'nivel_acesso' in data:
                usuario.nivel_acesso = data['nivel_acesso']
            if 'ativo' in data:
                usuario.ativo = data['ativo']
        
        db.session.commit()
        
        # Registrar atividade
        atividade = HistoricoAtividade(
            usuario_id=usuario_atual_id,
            acao='atualizar_usuario',
            detalhes=f'Usuário {usuario.email} atualizado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(usuario.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@usuarios_bp.route('/<usuario_id>', methods=['DELETE'])
@jwt_required()
def deletar_usuario(usuario_id):
    """Deleta um usuário (apenas admins)"""
    try:
        if not verificar_permissao_admin():
            return jsonify({'erro': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        # Não permitir deletar o próprio usuário
        usuario_atual_id = get_jwt_identity()
        if usuario_atual_id == usuario_id:
            return jsonify({'erro': 'Não é possível deletar seu próprio usuário'}), 400
        
        email_deletado = usuario.email
        db.session.delete(usuario)
        db.session.commit()
        
        # Registrar atividade
        atividade = HistoricoAtividade(
            usuario_id=usuario_atual_id,
            acao='deletar_usuario',
            detalhes=f'Usuário {email_deletado} deletado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({'mensagem': 'Usuário deletado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

