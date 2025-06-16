from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(50), nullable=False)  # admin, vallet, caixa, atendente
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'nivel_acesso': self.nivel_acesso,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    veiculos = db.relationship('Veiculo', backref='cliente', lazy=True)
    reservas = db.relationship('Reserva', backref='cliente', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = db.Column(db.String(36), db.ForeignKey('clientes.id'), nullable=False)
    placa = db.Column(db.String(10), nullable=False, unique=True)
    tipo_veiculo = db.Column(db.String(50), nullable=False)  # pequeno, grande, moto
    modelo = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    estacionamentos = db.relationship('Estacionamento', backref='veiculo', lazy=True)
    reservas = db.relationship('Reserva', backref='veiculo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'placa': self.placa,
            'tipo_veiculo': self.tipo_veiculo,
            'modelo': self.modelo,
            'cor': self.cor,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Vaga(db.Model):
    __tablename__ = 'vagas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    numero_vaga = db.Column(db.String(10), nullable=False, unique=True)
    tipo_vaga = db.Column(db.String(50), nullable=False)  # pequena, grande, moto, reservada
    status = db.Column(db.String(50), nullable=False, default='disponivel')  # disponivel, ocupada, manutencao
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    estacionamentos = db.relationship('Estacionamento', backref='vaga', lazy=True)
    reservas = db.relationship('Reserva', backref='vaga', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_vaga': self.numero_vaga,
            'tipo_vaga': self.tipo_vaga,
            'status': self.status,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Estacionamento(db.Model):
    __tablename__ = 'estacionamentos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    veiculo_id = db.Column(db.String(36), db.ForeignKey('veiculos.id'), nullable=False)
    vaga_id = db.Column(db.String(36), db.ForeignKey('vagas.id'), nullable=False)
    entrada_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    saida_em = db.Column(db.DateTime)
    status = db.Column(db.String(50), nullable=False, default='aberto')  # aberto, encerrado, cancelado
    tiquete_qr_code = db.Column(db.String(255), unique=True)
    criado_por = db.Column(db.String(36), db.ForeignKey('usuarios.id'), nullable=False)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    pagamentos = db.relationship('Pagamento', backref='estacionamento', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'veiculo_id': self.veiculo_id,
            'vaga_id': self.vaga_id,
            'entrada_em': self.entrada_em.isoformat(),
            'saida_em': self.saida_em.isoformat() if self.saida_em else None,
            'status': self.status,
            'tiquete_qr_code': self.tiquete_qr_code,
            'criado_por': self.criado_por,
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Tarifa(db.Model):
    __tablename__ = 'tarifas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    unidade_tempo = db.Column(db.String(50), nullable=False)  # hora, dia, minuto
    tipo_veiculo = db.Column(db.String(50))
    dia_semana = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'valor': float(self.valor),
            'unidade_tempo': self.unidade_tempo,
            'tipo_veiculo': self.tipo_veiculo,
            'dia_semana': self.dia_semana,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    estacionamento_id = db.Column(db.String(36), db.ForeignKey('estacionamentos.id'), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)  # cartao, dinheiro, pix
    status = db.Column(db.String(50), nullable=False, default='pendente')  # pendente, confirmado, cancelado
    data_pagamento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comprovante_url = db.Column(db.Text)
    processado_por = db.Column(db.String(36), db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'estacionamento_id': self.estacionamento_id,
            'valor_total': float(self.valor_total),
            'forma_pagamento': self.forma_pagamento,
            'status': self.status,
            'data_pagamento': self.data_pagamento.isoformat(),
            'comprovante_url': self.comprovante_url,
            'processado_por': self.processado_por,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class Reserva(db.Model):
    __tablename__ = 'reservas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = db.Column(db.String(36), db.ForeignKey('clientes.id'), nullable=False)
    veiculo_id = db.Column(db.String(36), db.ForeignKey('veiculos.id'), nullable=False)
    vaga_id = db.Column(db.String(36), db.ForeignKey('vagas.id'))
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pendente')  # pendente, confirmada, cancelada, concluida
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'veiculo_id': self.veiculo_id,
            'vaga_id': self.vaga_id,
            'data_hora_inicio': self.data_hora_inicio.isoformat(),
            'data_hora_fim': self.data_hora_fim.isoformat(),
            'status': self.status,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }

class HistoricoAtividade(db.Model):
    __tablename__ = 'historico_atividades'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = db.Column(db.String(36), db.ForeignKey('usuarios.id'), nullable=False)
    acao = db.Column(db.String(255), nullable=False)
    detalhes = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'acao': self.acao,
            'detalhes': self.detalhes,
            'data_hora': self.data_hora.isoformat()
        }

