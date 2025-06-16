from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Vaga, HistoricoAtividade

vagas_bp = Blueprint('vagas', __name__)

@vagas_bp.route('/', methods=['GET'])
@jwt_required()
def listar_vagas():
    """Lista todas as vagas com filtros opcionais"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        tipo_vaga = request.args.get('tipo_vaga')
        numero_vaga = request.args.get('numero_vaga')
        
        query = Vaga.query
        
        # Aplicar filtros
        if status:
            query = query.filter(Vaga.status == status)
        if tipo_vaga:
            query = query.filter(Vaga.tipo_vaga == tipo_vaga)
        if numero_vaga:
            query = query.filter(Vaga.numero_vaga.ilike(f'%{numero_vaga}%'))
        
        vagas = query.order_by(Vaga.numero_vaga).all()
        return jsonify([vaga.to_dict() for vaga in vagas]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/disponiveis', methods=['GET'])
@jwt_required()
def listar_vagas_disponiveis():
    """Lista apenas vagas disponíveis"""
    try:
        tipo_vaga = request.args.get('tipo_vaga')
        
        query = Vaga.query.filter(Vaga.status == 'disponivel')
        
        if tipo_vaga:
            query = query.filter(Vaga.tipo_vaga == tipo_vaga)
        
        vagas = query.order_by(Vaga.numero_vaga).all()
        return jsonify([vaga.to_dict() for vaga in vagas]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/ocupacao', methods=['GET'])
@jwt_required()
def obter_ocupacao():
    """Obtém estatísticas de ocupação das vagas"""
    try:
        total_vagas = Vaga.query.count()
        vagas_ocupadas = Vaga.query.filter(Vaga.status == 'ocupada').count()
        vagas_disponiveis = Vaga.query.filter(Vaga.status == 'disponivel').count()
        vagas_manutencao = Vaga.query.filter(Vaga.status == 'manutencao').count()
        
        # Estatísticas por tipo
        tipos_vaga = db.session.query(Vaga.tipo_vaga).distinct().all()
        ocupacao_por_tipo = {}
        
        for (tipo,) in tipos_vaga:
            total_tipo = Vaga.query.filter(Vaga.tipo_vaga == tipo).count()
            ocupadas_tipo = Vaga.query.filter(Vaga.tipo_vaga == tipo, Vaga.status == 'ocupada').count()
            ocupacao_por_tipo[tipo] = {
                'total': total_tipo,
                'ocupadas': ocupadas_tipo,
                'disponiveis': total_tipo - ocupadas_tipo,
                'percentual_ocupacao': round((ocupadas_tipo / total_tipo * 100) if total_tipo > 0 else 0, 2)
            }
        
        return jsonify({
            'total_vagas': total_vagas,
            'vagas_ocupadas': vagas_ocupadas,
            'vagas_disponiveis': vagas_disponiveis,
            'vagas_manutencao': vagas_manutencao,
            'percentual_ocupacao': round((vagas_ocupadas / total_vagas * 100) if total_vagas > 0 else 0, 2),
            'ocupacao_por_tipo': ocupacao_por_tipo
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/', methods=['POST'])
@jwt_required()
def criar_vaga():
    """Cria uma nova vaga"""
    try:
        data = request.get_json()
        
        # Validações
        campos_obrigatorios = ['numero_vaga', 'tipo_vaga']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'{campo} é obrigatório'}), 400
        
        # Verificar se número da vaga já existe
        if Vaga.query.filter_by(numero_vaga=data['numero_vaga']).first():
            return jsonify({'erro': 'Número da vaga já existe'}), 400
        
        # Criar vaga
        vaga = Vaga(
            numero_vaga=data['numero_vaga'],
            tipo_vaga=data['tipo_vaga'],
            status=data.get('status', 'disponivel')
        )
        
        db.session.add(vaga)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='criar_vaga',
            detalhes=f'Vaga {vaga.numero_vaga} criada'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(vaga.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/<vaga_id>', methods=['GET'])
@jwt_required()
def obter_vaga(vaga_id):
    """Obtém uma vaga específica"""
    try:
        vaga = Vaga.query.get(vaga_id)
        if not vaga:
            return jsonify({'erro': 'Vaga não encontrada'}), 404
        
        return jsonify(vaga.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/<vaga_id>', methods=['PUT'])
@jwt_required()
def atualizar_vaga(vaga_id):
    """Atualiza uma vaga"""
    try:
        vaga = Vaga.query.get(vaga_id)
        if not vaga:
            return jsonify({'erro': 'Vaga não encontrada'}), 404
        
        data = request.get_json()
        
        # Atualizar campos
        if 'numero_vaga' in data:
            # Verificar se número já existe (exceto a própria vaga)
            numero_existente = Vaga.query.filter_by(numero_vaga=data['numero_vaga']).first()
            if numero_existente and numero_existente.id != vaga_id:
                return jsonify({'erro': 'Número da vaga já existe'}), 400
            vaga.numero_vaga = data['numero_vaga']
        if 'tipo_vaga' in data:
            vaga.tipo_vaga = data['tipo_vaga']
        if 'status' in data:
            vaga.status = data['status']
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='atualizar_vaga',
            detalhes=f'Vaga {vaga.numero_vaga} atualizada'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(vaga.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/<vaga_id>', methods=['DELETE'])
@jwt_required()
def deletar_vaga(vaga_id):
    """Deleta uma vaga"""
    try:
        vaga = Vaga.query.get(vaga_id)
        if not vaga:
            return jsonify({'erro': 'Vaga não encontrada'}), 404
        
        # Verificar se vaga está ocupada
        if vaga.status == 'ocupada':
            return jsonify({'erro': 'Não é possível deletar vaga ocupada'}), 400
        
        # Verificar se vaga tem estacionamentos ativos
        estacionamentos_ativos = [e for e in vaga.estacionamentos if e.status == 'aberto']
        if estacionamentos_ativos:
            return jsonify({'erro': 'Não é possível deletar vaga com estacionamentos ativos'}), 400
        
        numero_deletado = vaga.numero_vaga
        db.session.delete(vaga)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='deletar_vaga',
            detalhes=f'Vaga {numero_deletado} deletada'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({'mensagem': 'Vaga deletada com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/<vaga_id>/ocupar', methods=['POST'])
@jwt_required()
def ocupar_vaga(vaga_id):
    """Marca uma vaga como ocupada"""
    try:
        vaga = Vaga.query.get(vaga_id)
        if not vaga:
            return jsonify({'erro': 'Vaga não encontrada'}), 404
        
        if vaga.status != 'disponivel':
            return jsonify({'erro': 'Vaga não está disponível'}), 400
        
        vaga.status = 'ocupada'
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='ocupar_vaga',
            detalhes=f'Vaga {vaga.numero_vaga} ocupada'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(vaga.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@vagas_bp.route('/<vaga_id>/liberar', methods=['POST'])
@jwt_required()
def liberar_vaga(vaga_id):
    """Marca uma vaga como disponível"""
    try:
        vaga = Vaga.query.get(vaga_id)
        if not vaga:
            return jsonify({'erro': 'Vaga não encontrada'}), 404
        
        if vaga.status != 'ocupada':
            return jsonify({'erro': 'Vaga não está ocupada'}), 400
        
        vaga.status = 'disponivel'
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='liberar_vaga',
            detalhes=f'Vaga {vaga.numero_vaga} liberada'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(vaga.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

