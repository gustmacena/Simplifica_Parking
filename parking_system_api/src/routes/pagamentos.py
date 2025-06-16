from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Pagamento, Estacionamento, Tarifa, HistoricoAtividade
from datetime import datetime

pagamentos_bp = Blueprint('pagamentos', __name__)

def calcular_valor_estacionamento(estacionamento):
    """Calcula o valor a ser pago pelo estacionamento"""
    try:
        # Buscar tarifa padrão (simplificado - pode ser expandido)
        tarifa = Tarifa.query.filter(Tarifa.ativo == True).first()
        
        if not tarifa:
            # Tarifa padrão se não houver configurada
            valor_hora = 5.00
        else:
            valor_hora = float(tarifa.valor)
        
        # Calcular tempo de permanência
        entrada = estacionamento.entrada_em
        saida = estacionamento.saida_em if estacionamento.saida_em else datetime.utcnow()
        
        tempo_total = saida - entrada
        horas = tempo_total.total_seconds() / 3600
        
        # Mínimo de 1 hora
        if horas < 1:
            horas = 1
        
        # Arredondar para cima (frações de hora são cobradas como hora completa)
        import math
        horas_cobranca = math.ceil(horas)
        
        valor_total = horas_cobranca * valor_hora
        
        return {
            'valor_total': valor_total,
            'horas_cobranca': horas_cobranca,
            'valor_hora': valor_hora,
            'tempo_permanencia': horas
        }
        
    except Exception as e:
        return {'erro': str(e)}

@pagamentos_bp.route('/', methods=['GET'])
@jwt_required()
def listar_pagamentos():
    """Lista todos os pagamentos com filtros opcionais"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        forma_pagamento = request.args.get('forma_pagamento')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        estacionamento_id = request.args.get('estacionamento_id')
        
        query = Pagamento.query
        
        # Aplicar filtros
        if status:
            query = query.filter(Pagamento.status == status)
        if forma_pagamento:
            query = query.filter(Pagamento.forma_pagamento == forma_pagamento)
        if estacionamento_id:
            query = query.filter(Pagamento.estacionamento_id == estacionamento_id)
        if data_inicio:
            query = query.filter(Pagamento.data_pagamento >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(Pagamento.data_pagamento <= datetime.fromisoformat(data_fim))
        
        pagamentos = query.order_by(Pagamento.data_pagamento.desc()).all()
        return jsonify([pagamento.to_dict() for pagamento in pagamentos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/calcular/<estacionamento_id>', methods=['GET'])
@jwt_required()
def calcular_pagamento(estacionamento_id):
    """Calcula o valor a ser pago por um estacionamento"""
    try:
        estacionamento = Estacionamento.query.get(estacionamento_id)
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        calculo = calcular_valor_estacionamento(estacionamento)
        
        if 'erro' in calculo:
            return jsonify({'erro': calculo['erro']}), 500
        
        return jsonify(calculo), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/', methods=['POST'])
@jwt_required()
def processar_pagamento():
    """Processa um pagamento"""
    try:
        data = request.get_json()
        
        # Validações
        campos_obrigatorios = ['estacionamento_id', 'forma_pagamento']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'{campo} é obrigatório'}), 400
        
        # Verificar se estacionamento existe
        estacionamento = Estacionamento.query.get(data['estacionamento_id'])
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        # Verificar se já existe pagamento para este estacionamento
        pagamento_existente = Pagamento.query.filter_by(
            estacionamento_id=data['estacionamento_id']
        ).first()
        
        if pagamento_existente:
            return jsonify({'erro': 'Pagamento já foi processado para este estacionamento'}), 400
        
        # Calcular valor
        calculo = calcular_valor_estacionamento(estacionamento)
        if 'erro' in calculo:
            return jsonify({'erro': calculo['erro']}), 500
        
        # Usar valor calculado ou valor informado
        valor_total = data.get('valor_total', calculo['valor_total'])
        
        # Criar pagamento
        pagamento = Pagamento(
            estacionamento_id=data['estacionamento_id'],
            valor_total=valor_total,
            forma_pagamento=data['forma_pagamento'],
            status=data.get('status', 'confirmado'),
            comprovante_url=data.get('comprovante_url'),
            processado_por=get_jwt_identity()
        )
        
        db.session.add(pagamento)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='processar_pagamento',
            detalhes=f'Pagamento de R$ {valor_total:.2f} processado via {data["forma_pagamento"]}'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(pagamento.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/<pagamento_id>', methods=['GET'])
@jwt_required()
def obter_pagamento(pagamento_id):
    """Obtém um pagamento específico"""
    try:
        pagamento = Pagamento.query.get(pagamento_id)
        if not pagamento:
            return jsonify({'erro': 'Pagamento não encontrado'}), 404
        
        return jsonify(pagamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/<pagamento_id>', methods=['PUT'])
@jwt_required()
def atualizar_pagamento(pagamento_id):
    """Atualiza um pagamento"""
    try:
        pagamento = Pagamento.query.get(pagamento_id)
        if not pagamento:
            return jsonify({'erro': 'Pagamento não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'status' in data:
            pagamento.status = data['status']
        if 'comprovante_url' in data:
            pagamento.comprovante_url = data['comprovante_url']
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='atualizar_pagamento',
            detalhes=f'Pagamento {pagamento.id} atualizado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(pagamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/<pagamento_id>/cancelar', methods=['POST'])
@jwt_required()
def cancelar_pagamento(pagamento_id):
    """Cancela um pagamento"""
    try:
        pagamento = Pagamento.query.get(pagamento_id)
        if not pagamento:
            return jsonify({'erro': 'Pagamento não encontrado'}), 404
        
        if pagamento.status == 'cancelado':
            return jsonify({'erro': 'Pagamento já foi cancelado'}), 400
        
        pagamento.status = 'cancelado'
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='cancelar_pagamento',
            detalhes=f'Pagamento {pagamento.id} cancelado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(pagamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/estacionamento/<estacionamento_id>', methods=['GET'])
@jwt_required()
def obter_pagamento_por_estacionamento(estacionamento_id):
    """Obtém pagamento de um estacionamento específico"""
    try:
        pagamento = Pagamento.query.filter_by(estacionamento_id=estacionamento_id).first()
        if not pagamento:
            return jsonify({'erro': 'Pagamento não encontrado'}), 404
        
        return jsonify(pagamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pagamentos_bp.route('/resumo', methods=['GET'])
@jwt_required()
def obter_resumo_pagamentos():
    """Obtém resumo dos pagamentos"""
    try:
        # Parâmetros de filtro de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Pagamento.query
        
        if data_inicio:
            query = query.filter(Pagamento.data_pagamento >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(Pagamento.data_pagamento <= datetime.fromisoformat(data_fim))
        
        # Estatísticas gerais
        total_pagamentos = query.count()
        pagamentos_confirmados = query.filter(Pagamento.status == 'confirmado').count()
        pagamentos_pendentes = query.filter(Pagamento.status == 'pendente').count()
        pagamentos_cancelados = query.filter(Pagamento.status == 'cancelado').count()
        
        # Valor total arrecadado
        valor_total = db.session.query(db.func.sum(Pagamento.valor_total)).filter(
            Pagamento.status == 'confirmado'
        )
        
        if data_inicio:
            valor_total = valor_total.filter(Pagamento.data_pagamento >= datetime.fromisoformat(data_inicio))
        if data_fim:
            valor_total = valor_total.filter(Pagamento.data_pagamento <= datetime.fromisoformat(data_fim))
        
        valor_total = valor_total.scalar() or 0
        
        # Pagamentos por forma de pagamento
        formas_pagamento = db.session.query(
            Pagamento.forma_pagamento,
            db.func.count(Pagamento.id).label('quantidade'),
            db.func.sum(Pagamento.valor_total).label('valor_total')
        ).filter(Pagamento.status == 'confirmado')
        
        if data_inicio:
            formas_pagamento = formas_pagamento.filter(Pagamento.data_pagamento >= datetime.fromisoformat(data_inicio))
        if data_fim:
            formas_pagamento = formas_pagamento.filter(Pagamento.data_pagamento <= datetime.fromisoformat(data_fim))
        
        formas_pagamento = formas_pagamento.group_by(Pagamento.forma_pagamento).all()
        
        resumo_formas = {}
        for forma, quantidade, valor in formas_pagamento:
            resumo_formas[forma] = {
                'quantidade': quantidade,
                'valor_total': float(valor or 0)
            }
        
        return jsonify({
            'total_pagamentos': total_pagamentos,
            'pagamentos_confirmados': pagamentos_confirmados,
            'pagamentos_pendentes': pagamentos_pendentes,
            'pagamentos_cancelados': pagamentos_cancelados,
            'valor_total_arrecadado': float(valor_total),
            'resumo_por_forma_pagamento': resumo_formas
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

