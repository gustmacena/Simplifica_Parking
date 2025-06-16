from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Cliente, HistoricoAtividade
from sqlalchemy import or_

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/', methods=['GET'])
@jwt_required()
def listar_clientes():
    """Lista todos os clientes com filtros opcionais"""
    try:
        # Parâmetros de filtro
        nome = request.args.get('nome')
        cpf = request.args.get('cpf')
        telefone = request.args.get('telefone')
        
        query = Cliente.query
        
        # Aplicar filtros
        if nome:
            query = query.filter(Cliente.nome.ilike(f'%{nome}%'))
        if cpf:
            query = query.filter(Cliente.cpf.like(f'%{cpf}%'))
        if telefone:
            query = query.filter(Cliente.telefone.like(f'%{telefone}%'))
        
        clientes = query.all()
        return jsonify([cliente.to_dict() for cliente in clientes]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_clientes():
    """Busca clientes por termo geral"""
    try:
        termo = request.args.get('termo', '')
        
        if not termo:
            return jsonify([]), 200
        
        clientes = Cliente.query.filter(
            or_(
                Cliente.nome.ilike(f'%{termo}%'),
                Cliente.cpf.like(f'%{termo}%'),
                Cliente.telefone.like(f'%{termo}%')
            )
        ).all()
        
        return jsonify([cliente.to_dict() for cliente in clientes]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/', methods=['POST'])
@jwt_required()
def criar_cliente():
    """Cria um novo cliente"""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('nome'):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        # Verificar se CPF já existe (se fornecido)
        if data.get('cpf'):
            if Cliente.query.filter_by(cpf=data['cpf']).first():
                return jsonify({'erro': 'CPF já cadastrado'}), 400
        
        # Criar cliente
        cliente = Cliente(
            nome=data['nome'],
            cpf=data.get('cpf'),
            telefone=data.get('telefone'),
            endereco=data.get('endereco')
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='criar_cliente',
            detalhes=f'Cliente {cliente.nome} criado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/<cliente_id>', methods=['GET'])
@jwt_required()
def obter_cliente(cliente_id):
    """Obtém um cliente específico"""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        return jsonify(cliente.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/<cliente_id>', methods=['PUT'])
@jwt_required()
def atualizar_cliente(cliente_id):
    """Atualiza um cliente"""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos
        if 'nome' in data:
            cliente.nome = data['nome']
        if 'cpf' in data:
            # Verificar se CPF já existe (exceto o próprio cliente)
            if data['cpf']:
                cpf_existente = Cliente.query.filter_by(cpf=data['cpf']).first()
                if cpf_existente and cpf_existente.id != cliente_id:
                    return jsonify({'erro': 'CPF já cadastrado'}), 400
            cliente.cpf = data['cpf']
        if 'telefone' in data:
            cliente.telefone = data['telefone']
        if 'endereco' in data:
            cliente.endereco = data['endereco']
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='atualizar_cliente',
            detalhes=f'Cliente {cliente.nome} atualizado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/<cliente_id>', methods=['DELETE'])
@jwt_required()
def deletar_cliente(cliente_id):
    """Deleta um cliente"""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        # Verificar se cliente tem veículos ou reservas ativas
        if cliente.veiculos:
            return jsonify({'erro': 'Não é possível deletar cliente com veículos cadastrados'}), 400
        
        reservas_ativas = [r for r in cliente.reservas if r.status in ['pendente', 'confirmada']]
        if reservas_ativas:
            return jsonify({'erro': 'Não é possível deletar cliente com reservas ativas'}), 400
        
        nome_deletado = cliente.nome
        db.session.delete(cliente)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='deletar_cliente',
            detalhes=f'Cliente {nome_deletado} deletado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({'mensagem': 'Cliente deletado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@clientes_bp.route('/<cliente_id>/veiculos', methods=['GET'])
@jwt_required()
def listar_veiculos_cliente(cliente_id):
    """Lista todos os veículos de um cliente"""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        return jsonify([veiculo.to_dict() for veiculo in cliente.veiculos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

