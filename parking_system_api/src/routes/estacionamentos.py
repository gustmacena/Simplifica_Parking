from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Estacionamento, Veiculo, Vaga, HistoricoAtividade
from datetime import datetime
import uuid
import qrcode
import io
import base64

estacionamentos_bp = Blueprint('estacionamentos', __name__)

def gerar_qr_code():
    """Gera um código QR único para o tíquete"""
    return str(uuid.uuid4())

@estacionamentos_bp.route('/', methods=['GET'])
@jwt_required()
def listar_estacionamentos():
    """Lista todos os estacionamentos com filtros opcionais"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        veiculo_id = request.args.get('veiculo_id')
        vaga_id = request.args.get('vaga_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Estacionamento.query
        
        # Aplicar filtros
        if status:
            query = query.filter(Estacionamento.status == status)
        if veiculo_id:
            query = query.filter(Estacionamento.veiculo_id == veiculo_id)
        if vaga_id:
            query = query.filter(Estacionamento.vaga_id == vaga_id)
        if data_inicio:
            query = query.filter(Estacionamento.entrada_em >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(Estacionamento.entrada_em <= datetime.fromisoformat(data_fim))
        
        estacionamentos = query.order_by(Estacionamento.entrada_em.desc()).all()
        return jsonify([estacionamento.to_dict() for estacionamento in estacionamentos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/ativos', methods=['GET'])
@jwt_required()
def listar_estacionamentos_ativos():
    """Lista apenas estacionamentos ativos (abertos)"""
    try:
        estacionamentos = Estacionamento.query.filter(
            Estacionamento.status == 'aberto'
        ).order_by(Estacionamento.entrada_em.desc()).all()
        
        return jsonify([estacionamento.to_dict() for estacionamento in estacionamentos]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/', methods=['POST'])
@jwt_required()
def criar_estacionamento():
    """Registra entrada de veículo no estacionamento"""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('veiculo_id'):
            return jsonify({'erro': 'ID do veículo é obrigatório'}), 400
        
        # Verificar se veículo existe
        veiculo = Veiculo.query.get(data['veiculo_id'])
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
        
        # Verificar se veículo já está estacionado
        estacionamento_ativo = Estacionamento.query.filter(
            Estacionamento.veiculo_id == data['veiculo_id'],
            Estacionamento.status == 'aberto'
        ).first()
        
        if estacionamento_ativo:
            return jsonify({'erro': 'Veículo já está estacionado'}), 400
        
        # Buscar vaga disponível do tipo compatível
        vaga = None
        if data.get('vaga_id'):
            # Vaga específica foi solicitada
            vaga = Vaga.query.get(data['vaga_id'])
            if not vaga:
                return jsonify({'erro': 'Vaga não encontrada'}), 404
            if vaga.status != 'disponivel':
                return jsonify({'erro': 'Vaga não está disponível'}), 400
        else:
            # Buscar vaga disponível automaticamente
            vaga = Vaga.query.filter(
                Vaga.status == 'disponivel',
                Vaga.tipo_vaga.in_(['pequena', 'grande']) if veiculo.tipo_veiculo in ['pequeno', 'grande'] else Vaga.tipo_vaga == 'moto'
            ).first()
            
            if not vaga:
                return jsonify({'erro': 'Nenhuma vaga disponível para este tipo de veículo'}), 400
        
        # Gerar código QR para o tíquete
        qr_code = gerar_qr_code()
        
        # Criar estacionamento
        estacionamento = Estacionamento(
            veiculo_id=data['veiculo_id'],
            vaga_id=vaga.id,
            tiquete_qr_code=qr_code,
            criado_por=get_jwt_identity()
        )
        
        # Marcar vaga como ocupada
        vaga.status = 'ocupada'
        
        db.session.add(estacionamento)
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='entrada_veiculo',
            detalhes=f'Veículo {veiculo.placa} entrou na vaga {vaga.numero_vaga}'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(estacionamento.to_dict()), 201
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/<estacionamento_id>', methods=['GET'])
@jwt_required()
def obter_estacionamento(estacionamento_id):
    """Obtém um estacionamento específico"""
    try:
        estacionamento = Estacionamento.query.get(estacionamento_id)
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        return jsonify(estacionamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/<estacionamento_id>/encerrar', methods=['POST'])
@jwt_required()
def encerrar_estacionamento(estacionamento_id):
    """Registra saída de veículo do estacionamento"""
    try:
        estacionamento = Estacionamento.query.get(estacionamento_id)
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        if estacionamento.status != 'aberto':
            return jsonify({'erro': 'Estacionamento já foi encerrado'}), 400
        
        # Atualizar estacionamento
        estacionamento.saida_em = datetime.utcnow()
        estacionamento.status = 'encerrado'
        
        # Liberar vaga
        vaga = Vaga.query.get(estacionamento.vaga_id)
        if vaga:
            vaga.status = 'disponivel'
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        veiculo = Veiculo.query.get(estacionamento.veiculo_id)
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='saida_veiculo',
            detalhes=f'Veículo {veiculo.placa if veiculo else "N/A"} saiu da vaga {vaga.numero_vaga if vaga else "N/A"}'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(estacionamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/<estacionamento_id>/cancelar', methods=['POST'])
@jwt_required()
def cancelar_estacionamento(estacionamento_id):
    """Cancela um estacionamento"""
    try:
        estacionamento = Estacionamento.query.get(estacionamento_id)
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        if estacionamento.status != 'aberto':
            return jsonify({'erro': 'Estacionamento já foi finalizado'}), 400
        
        # Atualizar estacionamento
        estacionamento.status = 'cancelado'
        
        # Liberar vaga
        vaga = Vaga.query.get(estacionamento.vaga_id)
        if vaga:
            vaga.status = 'disponivel'
        
        db.session.commit()
        
        # Registrar atividade
        usuario_id = get_jwt_identity()
        veiculo = Veiculo.query.get(estacionamento.veiculo_id)
        atividade = HistoricoAtividade(
            usuario_id=usuario_id,
            acao='cancelar_estacionamento',
            detalhes=f'Estacionamento do veículo {veiculo.placa if veiculo else "N/A"} cancelado'
        )
        db.session.add(atividade)
        db.session.commit()
        
        return jsonify(estacionamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/qrcode/<qr_code>', methods=['GET'])
@jwt_required()
def buscar_por_qrcode(qr_code):
    """Busca estacionamento por código QR"""
    try:
        estacionamento = Estacionamento.query.filter_by(tiquete_qr_code=qr_code).first()
        if not estacionamento:
            return jsonify({'erro': 'Tíquete não encontrado'}), 404
        
        return jsonify(estacionamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/veiculo/<veiculo_id>/ativo', methods=['GET'])
@jwt_required()
def obter_estacionamento_ativo_veiculo(veiculo_id):
    """Obtém estacionamento ativo de um veículo específico"""
    try:
        estacionamento = Estacionamento.query.filter(
            Estacionamento.veiculo_id == veiculo_id,
            Estacionamento.status == 'aberto'
        ).first()
        
        if not estacionamento:
            return jsonify({'erro': 'Veículo não está estacionado'}), 404
        
        return jsonify(estacionamento.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@estacionamentos_bp.route('/tempo/<estacionamento_id>', methods=['GET'])
@jwt_required()
def calcular_tempo_estacionamento(estacionamento_id):
    """Calcula tempo de permanência no estacionamento"""
    try:
        estacionamento = Estacionamento.query.get(estacionamento_id)
        if not estacionamento:
            return jsonify({'erro': 'Estacionamento não encontrado'}), 404
        
        entrada = estacionamento.entrada_em
        saida = estacionamento.saida_em if estacionamento.saida_em else datetime.utcnow()
        
        tempo_total = saida - entrada
        horas = tempo_total.total_seconds() / 3600
        minutos = (tempo_total.total_seconds() % 3600) / 60
        
        return jsonify({
            'entrada': entrada.isoformat(),
            'saida': saida.isoformat() if estacionamento.saida_em else None,
            'tempo_total_segundos': int(tempo_total.total_seconds()),
            'tempo_total_horas': round(horas, 2),
            'tempo_formatado': f'{int(horas)}h {int(minutos)}min',
            'status': estacionamento.status
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

