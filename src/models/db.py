import logging
import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class Entry(Base):
    __tablename__ = 'entries'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    type = Column(String(20))
    amount = Column(Float, nullable=False)
    category = Column(String(100))
    description = Column(String(500))
    date = Column(DateTime, default=datetime.now)
    is_encrypted = Column(Boolean, default=False)

    def __repr__(self):
        return f'<Entry {self.id}: {self.type} R${self.amount} - {self.category}>'


class Bank(Base):
    __tablename__ = 'banks'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, unique=True)
    total_balance = Column(Float, default=0)
    currency = Column(String(10), default='BRL')
    last_updated = Column(DateTime, default=datetime.now)
    last_month = Column(Integer, default=0)

    def __repr__(self):
        return f'<Bank {self.user_id}: R${self.total_balance}>'


def init_db(db_uri=None):
    """Inicializa o banco a partir de DB_URI ou da conexão PostgreSQL local padrão.

    Exemplos:
    - PostgreSQL: postgresql://localhost/bot_financeiro
    - SQLite: sqlite:///bot_financeiro.db
    """
    db_uri = db_uri or os.getenv(
        'DB_URI',
        'postgresql://localhost:5432/bot_financeiro',
    )
    logger.info('Conectando ao banco de dados')

    engine = create_engine(db_uri, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    logger.info('Banco de dados inicializado com sucesso')
    return {
        'engine': engine,
        'Session': Session,
        'Entry': Entry,
        'Bank': Bank,
    }
