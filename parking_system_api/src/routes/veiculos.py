from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Veiculo, Cliente, HistoricoAtividade
from sqlalchemy import or_

veiculos_bp = Blueprint('veiculos', __name__)

@veiculos_bp.route('/', methods=['GET'])
@jwt_required()
def listar_veiculos():
    """Lista todos os veículos com filtros opcionais"""
    try:
        # Parâmetros de filtro
        placa = request.args.get('placa')
        tipo_veiculo = request.args.get('tipo_veiculo')
        cliente_id = request.args.get('cliente_id')
        
        query = Veiculo.query
        
        # Aplicar filtros
        if placa:
            query = query.filter(Veiculo.placa.ilike(f'%{placa}%'))
        if tipo_veiculo:
            query = query.filter(Veiculo.tipo_veiculo == tipo_veiculo)
        if cliente_id:
            query = query.filter(Veiculo.cliente_id == cliente_id)
        
        veiculos = query.all()
        return jsonify([veiculo.to_dict() for veiculo in veiculos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_veiculos():
    """Busca veículos por termo geral"""
    try:
        termo = request.args.get('termo', '')
        
        if not termo:
            return jsonify([]), 200
        
        veiculos = Veiculo.query.filter(
            or_(
                Veiculo.placa.ilike(f'%{termo}%'),
                Veiculo.modelo.ilike(f'%{termo}%'),
                Veiculo.cor.ilike(f'%{termo}%')
            )
        ).all()
        
        return jsonify([veiculo.to_dict() for veiculo in veiculos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/', methods=['POST'])
@jwt_required()
def criar_veiculo():
    """Cria um novo veículo"""
    try:
        data = request.get_json()
        
        # Validações
        campos_obrigatorios = ['cliente_id', 'placa', 'tipo_veiculo']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'{campo} é obrigatório'}), 400
        
        # Verificar se cliente existe
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        # Verificar se placa já existe
        if Veiculo.query.filter_by(placa=data['placa']).first():
            return jsonify({'erro': 'Placa já cadastrada'}), 400
        
        # Criar veículo
        veiculo = Veiculo(
            cliente_id=data['cliente_id'],
            placa=data['placa'].upper(),
            tipo_veiculo=data['tipo_veiculo'],
            modelo=data.get('modelo'),
            cor=data.get('cor')
        )
        
        db.session.add(veiculo)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='criar_veiculo',
            detalhes=f'Veículo {veiculo.placa} criado para cliente {cliente.nome}'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(veiculo.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/<veiculo_id>', methods=['GET'])
@jwt_required()
def obter_veiculo(veiculo_id):
    """Obtém um veículo específico"""
    try:
        veiculo = Veiculo.query.get(veiculo_id)
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
        
        return jsonify(veiculo.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/<veiculo_id>', methods=['PUT'])
@jwt_required()
def atualizar_veiculo(veiculo_id):
    """Atualiza um veículo"""
    try:
        veiculo = Veiculo.query.get(veiculo_id)
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos
        if 'placa' in data:
            # Verificar se placa já existe (exceto o próprio veículo)
            placa_existente = Veiculo.query.filter_by(placa=data['placa']).first()
            if placa_existente and placa_existente.id != veiculo_id:
                return jsonify({'erro': 'Placa já cadastrada'}), 400
            veiculo.placa = data['placa'].upper()
        if 'tipo_veiculo' in data:
            veiculo.tipo_veiculo = data['tipo_veiculo']
        if 'modelo' in data:
            veiculo.modelo = data['modelo']
        if 'cor' in data:
            veiculo.cor = data['cor']
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='atualizar_veiculo',
            detalhes=f'Veículo {veiculo.placa} atualizado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(veiculo.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/<veiculo_id>', methods=['DELETE'])
@jwt_required()
def deletar_veiculo(veiculo_id):
    """Deleta um veículo"""
    try:
        veiculo = Veiculo.query.get(veiculo_id)
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
        
        # Verificar se veículo tem estacionamentos ativos
        estacionamentos_ativos = [e for e in veiculo.estacionamentos if e.status == 'aberto']
        if estacionamentos_ativos:
            return jsonify({'erro': 'Não é possível deletar veículo com estacionamentos ativos'}), 400
        
        placa_deletada = veiculo.placa
        db.session.delete(veiculo)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='deletar_veiculo',
            detalhes=f'Veículo {placa_deletada} deletado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({'mensagem': 'Veículo deletado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@veiculos_bp.route('/placa/<placa>', methods=['GET'])
@jwt_required()
def buscar_por_placa(placa):
    """Busca veículo por placa"""
    try:
        veiculo = Veiculo.query.filter_by(placa=placa.upper()).first()
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
        
        return jsonify(veiculo.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

