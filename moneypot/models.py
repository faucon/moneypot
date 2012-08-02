import transaction

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from sqlalchemy import (ForeignKey,
        Integer, Unicode, Enum, Float, Date, PickleType)

from formalchemy import Column
from formalchemy.validators import (
        required,
        email,
        )

from zope.sqlalchemy import ZopeTransactionExtension

from moneypot.utils import create_identifier, hash_password
from moneypot.utils import dummy_translate as _


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Pot(Base):
    '''
    This class describes a pot of money, it holds some information, and has relationships to participants, which in turn refer to their expenses
    '''
    __tablename__ = 'pot'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False, label=_(u'name'), nullable=False, validate=required)
    status = Column(Enum(u'open', u'closed', name='state'), default='open', nullable=False, validate=required)
    participants = relationship('Participant', backref='pot', lazy='immediate')

    def __init__(self, name=''):
        '''
        initialize a new pot with given values
        '''
        self.name = name

    @property
    def sum(self):
        '''returns the overall sum of expenses in this pot'''
        return sum([p.sum for p in self.participants])

    @property
    def share_factor_sum(self):
        '''sum of all participants share factors'''
        return sum([p.share_factor for p in self.participants])

    def expenses_sorted_by_date(self):
        '''all expenses in this pot, sorted ascending by date'''
        return DBSession.query(Expense).order_by('date').join(Participant).join(Pot).filter_by(id=self.id).all()


class Participant(Base):
    __tablename__ = 'participant'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=False, nullable=False, validate=required)
    email = Column(Unicode(255), nullable=True, validate=email)
    identifier = Column(Unicode(255), nullable=False, unique=True)
    share_factor = Column(Float(), default=1.0, nullable=False)
    pot_id = Column(Integer(), ForeignKey('pot.id'))
    expenses = relationship('Expense', backref='participant', lazy='immediate')
    user_id = Column(Integer(), ForeignKey('user.id'))

    def __init__(self, name=u'', email=u''):
        self.name = name
        self.email = email
        self.identifier = create_identifier(name)
        self.share_factor = 1

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.email)

    def add_expense(self, date, description, amount):
        self.expenses.append(Expense(date, description, amount))

    @property
    def sum(self):
        '''returns the sum of all expenses of this participant'''
        return sum([e.amount for e in self.expenses])

    @property
    def result(self):
        '''the amount of money this participant has to get (positive number) or to pay (negative number)'''
        return self.sum - self.share_factor / float(self.pot.share_factor_sum) * self.pot.sum   # attention to python divison! always use float!


class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    date = Column(Date(), nullable=False, validate=required)
    description = Column(Unicode(255), nullable=False, validate=required)
    amount = Column(Float(), nullable=False, validate=required)
    participant_id = Column(Integer(), ForeignKey('participant.id'))

    def __init__(self, date=None, description='', amount=''):
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
    username = Column(Unicode(255), unique=True)
    email = Column(Unicode(255))
    settings = Column(PickleType())
    password = Column(Unicode(255))
    participations = relationship('Participant', backref='user', lazy='immediate')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def __unicode__(self):
        return self.username

    def set_password(self, clear_passwd):
        '''
        set the password property, by hashing it with the utils.hash_password function
        '''
        self.password = hash_password(clear_passwd)

    def check_password(self, clear_passwd):
        '''
        check if the given password equals the stored one
        '''
        return self.password == hash_password(clear_passwd)

    @property
    def sum(self):
        '''returns the sum of all participation sums'''
        return sum([p.sum for p in self.participations])

    @property
    def result(self):
        '''the amount of money this user has to get (positive number) or to pay (negative number) in total of all his pots'''
        return sum([p.result for p in self.participations])


def populate():
    pass


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
