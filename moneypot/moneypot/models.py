import transaction

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.exc import IntegrityError

from sqlalchemy import (Column,
        Integer, Unicode, Enum, Float, Date, PickleType)


from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Pot(Base):
    __tablename__ = 'pot'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False)
    status = Column(Enum(u'open', u'closed', name='state'), default='open')

    def __init__(self, name='', value=''):
        self.name = name
        self.value = value


class Participant(Base):
    __tablename__ = 'participant'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False)
    email = Column(Unicode(255), nullable=True)
    identifier = Column(Unicode(255), nullable=True)

    def __init__(self, name='', email=''):
        self.name = name
        self.email = email


class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    date = Column(Date())
    description = Column(Unicode(255))
    amount = Column(Float())


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    date = Column(Date())
    status = Column(Enum(u'open', u'closed', name='state'), default='open')
    amount = Column(Float())


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255))
    email = Column(Unicode(255))
    settings = Column(PickleType())


def populate():
    session = DBSession()
    pot = Pot(name=u'test name')
    session.add(pot)
    session.flush()
    transaction.commit()


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    try:
        populate()
    except IntegrityError:
        transaction.abort()
    return DBSession


def appmaker(engine):
    initialize_sql(engine)
