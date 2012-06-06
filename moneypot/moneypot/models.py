import transaction

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from sqlalchemy import (Column, ForeignKey,
        Integer, Unicode, Enum, Float, Date, PickleType)


from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Pot(Base):
    '''
    This class describes a pot of money, it holds some information, and has relationships to participants, which in turn refer to their expenses
    '''
    __tablename__ = 'pot'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False)
    status = Column(Enum(u'open', u'closed', name='state'), default='open')
    participants = relationship('Participant', backref='pot')

    def __init__(self, name=''):
        '''
        initialize a new pot with given values
        '''
        self.name = name

    @property
    def sum(self):
        '''returns the overall sum of expenses in this pot'''
        return sum([p.sum for p in self.participants])


class Participant(Base):
    __tablename__ = 'participant'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False)
    email = Column(Unicode(255), nullable=True)
    identifier = Column(Unicode(255), nullable=True)
    pot_id = Column(Integer(), ForeignKey('pot.id'))
    expenses = relationship('Expense', backref='participant')

    def __init__(self, name='', email=''):
        self.name = name
        self.email = email

    def add_expense(self, date, description, amount):
        self.expenses.append(Expense(date, description, amount))

    @property
    def sum(self):
        '''returns the sum of all expenses of this participant'''
        return sum([e.amount for e in self.expenses])


class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    date = Column(Date())
    description = Column(Unicode(255))
    amount = Column(Float())
    participant_id = Column(Integer(), ForeignKey('participant.id'))

    def __init__(self, date, description, amount):
        self.date = date
        self.description = description
        self.amount = amount


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    date = Column(Date())
    status = Column(Enum(u'open', u'closed', name='state'), default='open')
    amount = Column(Float())
    from_participant_id = Column(Integer(), ForeignKey('participant.id'))
    to_participant_id = Column(Integer(), ForeignKey('participant.id'))

    from_participant = relationship(Participant, primaryjoin='Participant.id == Payment.from_participant_id')
    to_participant = relationship(Participant, primaryjoin='Participant.id == Payment.to_participant_id')


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
