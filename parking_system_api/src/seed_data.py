from werkzeug.security import generate_password_hash
from src.models.database import db, Usuario, Vaga, Tarifa
from datetime import datetime

def criar_dados_iniciais():
    """Cria dados iniciais para o sistema"""
    
    # Criar usuário administrador padrão
    admin_existente = Usuario.query.filter_by(email='admin@estacionamento.com').first()
    if not admin_existente:
        admin = Usuario(
            nome='Administrador',
            email='admin@estacionamento.com',
            senha_hash=generate_password_hash('admin123'),
            nivel_acesso='admin',
            ativo=True
        )
        db.session.add(admin)
    
    # Criar usuário vallet padrão
    vallet_existente = Usuario.query.filter_by(email='vallet@estacionamento.com').first()
    if not vallet_existente:
        vallet = Usuario(
            nome='Vallet Padrão',
            email='vallet@estacionamento.com',
            senha_hash=generate_password_hash('vallet123'),
            nivel_acesso='vallet',
            ativo=True
        )
        db.session.add(vallet)
    
    # Criar vagas padrão
    if Vaga.query.count() == 0:
        # Vagas pequenas (A1-A10)
        for i in range(1, 11):
            vaga = Vaga(
                numero_vaga=f'A{i:02d}',
                tipo_vaga='pequena',
                status='disponivel'
            )
            db.session.add(vaga)
        
        # Vagas grandes (B1-B10)
        for i in range(1, 11):
            vaga = Vaga(
                numero_vaga=f'B{i:02d}',
                tipo_vaga='grande',
                status='disponivel'
            )
            db.session.add(vaga)
        
        # Vagas para motos (M1-M5)
        for i in range(1, 6):
            vaga = Vaga(
                numero_vaga=f'M{i:02d}',
                tipo_vaga='moto',
                status='disponivel'
            )
            db.session.add(vaga)
    
    # Criar tarifas padrão
    if Tarifa.query.count() == 0:
        # Tarifa padrão por hora
        tarifa_hora = Tarifa(
            nome='Tarifa Padrão - Hora',
            valor=5.00,
            unidade_tempo='hora',
            ativo=True
        )
        db.session.add(tarifa_hora)
        
        # Tarifa para motos
        tarifa_moto = Tarifa(
            nome='Tarifa Moto - Hora',
            valor=3.00,
            unidade_tempo='hora',
            tipo_veiculo='moto',
            ativo=True
        )
        db.session.add(tarifa_moto)
        
        # Tarifa diária
        tarifa_diaria = Tarifa(
            nome='Tarifa Diária',
            valor=30.00,
            unidade_tempo='dia',
            ativo=True
        )
        db.session.add(tarifa_diaria)
    
    db.session.commit()
    print("Dados iniciais criados com sucesso!")

if __name__ == '__main__':
    from src.main import app
    with app.app_context():
        criar_dados_iniciais()

