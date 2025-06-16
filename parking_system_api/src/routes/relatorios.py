from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Estacionamento, Pagamento, Vaga, Cliente, Veiculo, HistoricoAtividade
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import io
import csv

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/ocupacao', methods=['GET'])
@jwt_required()
def relatorio_ocupacao():
    """Relatório de ocupação do estacionamento"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo_veiculo = request.args.get('tipo_veiculo')
        
        # Definir período padrão (último mês)
        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
        
        # Query base
        query = db.session.query(
            func.date(Estacionamento.entrada_em).label('data'),
            func.count(Estacionamento.id).label('total_entradas'),
            func.avg(
                func.extract('epoch', Estacionamento.saida_em - Estacionamento.entrada_em) / 3600
            ).label('tempo_medio_horas')
        ).filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        )
        
        # Filtro por tipo de veículo
        if tipo_veiculo:
            query = query.join(Veiculo).filter(Veiculo.tipo_veiculo == tipo_veiculo)
        
        # Agrupar por data
        ocupacao_diaria = query.group_by(func.date(Estacionamento.entrada_em)).all()
        
        # Estatísticas gerais
        total_estacionamentos = Estacionamento.query.filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        ).count()
        
        # Ocupação por tipo de vaga
        ocupacao_por_tipo = db.session.query(
            Vaga.tipo_vaga,
            func.count(Estacionamento.id).label('total_usos')
        ).join(Estacionamento).filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        ).group_by(Vaga.tipo_vaga).all()
        
        # Horários de pico
        horarios_pico = db.session.query(
            func.extract('hour', Estacionamento.entrada_em).label('hora'),
            func.count(Estacionamento.id).label('total_entradas')
        ).filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        ).group_by(func.extract('hour', Estacionamento.entrada_em)).all()
        
        return jsonify({
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'total_estacionamentos': total_estacionamentos,
            'ocupacao_diaria': [
                {
                    'data': str(data),
                    'total_entradas': total_entradas,
                    'tempo_medio_horas': round(float(tempo_medio_horas or 0), 2)
                }
                for data, total_entradas, tempo_medio_horas in ocupacao_diaria
            ],
            'ocupacao_por_tipo_vaga': [
                {
                    'tipo_vaga': tipo_vaga,
                    'total_usos': total_usos
                }
                for tipo_vaga, total_usos in ocupacao_por_tipo
            ],
            'horarios_pico': [
                {
                    'hora': int(hora),
                    'total_entradas': total_entradas
                }
                for hora, total_entradas in horarios_pico
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/faturamento', methods=['GET'])
@jwt_required()
def relatorio_faturamento():
    """Relatório de faturamento"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        forma_pagamento = request.args.get('forma_pagamento')
        
        # Definir período padrão (último mês)
        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
        
        # Query base
        query = Pagamento.query.filter(
            and_(
                Pagamento.data_pagamento >= data_inicio,
                Pagamento.data_pagamento <= data_fim,
                Pagamento.status == 'confirmado'
            )
        )
        
        # Filtro por forma de pagamento
        if forma_pagamento:
            query = query.filter(Pagamento.forma_pagamento == forma_pagamento)
        
        # Faturamento diário
        faturamento_diario = db.session.query(
            func.date(Pagamento.data_pagamento).label('data'),
            func.sum(Pagamento.valor_total).label('valor_total'),
            func.count(Pagamento.id).label('total_pagamentos')
        ).filter(
            and_(
                Pagamento.data_pagamento >= data_inicio,
                Pagamento.data_pagamento <= data_fim,
                Pagamento.status == 'confirmado'
            )
        ).group_by(func.date(Pagamento.data_pagamento)).all()
        
        # Faturamento por forma de pagamento
        faturamento_por_forma = db.session.query(
            Pagamento.forma_pagamento,
            func.sum(Pagamento.valor_total).label('valor_total'),
            func.count(Pagamento.id).label('total_pagamentos')
        ).filter(
            and_(
                Pagamento.data_pagamento >= data_inicio,
                Pagamento.data_pagamento <= data_fim,
                Pagamento.status == 'confirmado'
            )
        ).group_by(Pagamento.forma_pagamento).all()
        
        # Estatísticas gerais
        valor_total = db.session.query(func.sum(Pagamento.valor_total)).filter(
            and_(
                Pagamento.data_pagamento >= data_inicio,
                Pagamento.data_pagamento <= data_fim,
                Pagamento.status == 'confirmado'
            )
        ).scalar() or 0
        
        total_pagamentos = query.count()
        valor_medio = valor_total / total_pagamentos if total_pagamentos > 0 else 0
        
        return jsonify({
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'valor_total': float(valor_total),
            'total_pagamentos': total_pagamentos,
            'valor_medio': round(float(valor_medio), 2),
            'faturamento_diario': [
                {
                    'data': str(data),
                    'valor_total': float(valor_total),
                    'total_pagamentos': total_pagamentos
                }
                for data, valor_total, total_pagamentos in faturamento_diario
            ],
            'faturamento_por_forma_pagamento': [
                {
                    'forma_pagamento': forma_pagamento,
                    'valor_total': float(valor_total),
                    'total_pagamentos': total_pagamentos
                }
                for forma_pagamento, valor_total, total_pagamentos in faturamento_por_forma
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/clientes-frequentes', methods=['GET'])
@jwt_required()
def relatorio_clientes_frequentes():
    """Relatório de clientes mais frequentes"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        limite = int(request.args.get('limite', 10))
        
        # Definir período padrão (último mês)
        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
        
        # Clientes mais frequentes
        clientes_frequentes = db.session.query(
            Cliente.id,
            Cliente.nome,
            Cliente.cpf,
            func.count(Estacionamento.id).label('total_visitas'),
            func.sum(Pagamento.valor_total).label('valor_total_gasto')
        ).join(Veiculo).join(Estacionamento).outerjoin(Pagamento).filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        ).group_by(Cliente.id, Cliente.nome, Cliente.cpf).order_by(
            func.count(Estacionamento.id).desc()
        ).limit(limite).all()
        
        # Estatísticas de frequência
        total_clientes_unicos = db.session.query(func.count(func.distinct(Cliente.id))).join(
            Veiculo
        ).join(Estacionamento).filter(
            and_(
                Estacionamento.entrada_em >= data_inicio,
                Estacionamento.entrada_em <= data_fim
            )
        ).scalar()
        
        return jsonify({
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'total_clientes_unicos': total_clientes_unicos,
            'clientes_frequentes': [
                {
                    'cliente_id': cliente_id,
                    'nome': nome,
                    'cpf': cpf,
                    'total_visitas': total_visitas,
                    'valor_total_gasto': float(valor_total_gasto or 0)
                }
                for cliente_id, nome, cpf, total_visitas, valor_total_gasto in clientes_frequentes
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/atividades', methods=['GET'])
@jwt_required()
def relatorio_atividades():
    """Relatório de atividades dos usuários"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        usuario_id = request.args.get('usuario_id')
        acao = request.args.get('acao')
        
        # Definir período padrão (último mês)
        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
        
        # Query base
        query = HistoricoAtividade.query.filter(
            and_(
                HistoricoAtividade.data_hora >= data_inicio,
                HistoricoAtividade.data_hora <= data_fim
            )
        )
        
        # Filtros
        if usuario_id:
            query = query.filter(HistoricoAtividade.usuario_id == usuario_id)
        if acao:
            query = query.filter(HistoricoAtividade.acao == acao)
        
        # Atividades
        atividades = query.order_by(HistoricoAtividade.data_hora.desc()).limit(100).all()
        
        # Estatísticas por ação
        atividades_por_acao = db.session.query(
            HistoricoAtividade.acao,
            func.count(HistoricoAtividade.id).label('total')
        ).filter(
            and_(
                HistoricoAtividade.data_hora >= data_inicio,
                HistoricoAtividade.data_hora <= data_fim
            )
        ).group_by(HistoricoAtividade.acao).all()
        
        return jsonify({
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'atividades_recentes': [atividade.to_dict() for atividade in atividades],
            'estatisticas_por_acao': [
                {
                    'acao': acao,
                    'total': total
                }
                for acao, total in atividades_por_acao
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/exportar/faturamento', methods=['GET'])
@jwt_required()
def exportar_faturamento_csv():
    """Exporta relatório de faturamento em CSV"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Definir período padrão (último mês)
        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
        
        # Buscar dados
        pagamentos = Pagamento.query.filter(
            and_(
                Pagamento.data_pagamento >= data_inicio,
                Pagamento.data_pagamento <= data_fim,
                Pagamento.status == 'confirmado'
            )
        ).order_by(Pagamento.data_pagamento.desc()).all()
        
        # Criar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'Data Pagamento',
            'Valor Total',
            'Forma Pagamento',
            'Status',
            'ID Estacionamento'
        ])
        
        # Dados
        for pagamento in pagamentos:
            writer.writerow([
                pagamento.data_pagamento.strftime('%d/%m/%Y %H:%M'),
                f'R$ {pagamento.valor_total:.2f}',
                pagamento.forma_pagamento,
                pagamento.status,
                pagamento.estacionamento_id
            ])
        
        # Preparar arquivo para download
        output.seek(0)
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='exportar_relatorio',
            detalhes=f'Relatório de faturamento exportado (período: {data_inicio.date()} a {data_fim.date()})'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Relatório gerado com sucesso',
            'total_registros': len(pagamentos),
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

