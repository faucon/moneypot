import transaction

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from sqlalchemy import (ForeignKey, Integer, Unicode, Enum, Float, Date, PickleType)

from formalchemy import Column
from formalchemy.validators import (
    required,
    email,
)

from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.i18n import TranslationStringFactory
import csv

from moneypot.utils import create_identifier, hash_password
from moneypot.solver import MatchingSolver

_ = TranslationStringFactory('moneypot')


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Status(object):
    '''
    collect all possible status for pots
    the status will be set per participant
    '''
    OPEN = 'open'
    ARCHIVED = 'archived'

STATUS = Status()


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

    def close_and_solve(self):
        '''
        set status to closed and create payments for participants
        '''
        result = []
        solver = MatchingSolver()
        payments = solver.solve(self)
        for p in payments:
            result.append(Payment(*p))
        return result

    def write_csv(self, target):
        '''
        write list of expenses as a csv
        target should be file-like (should have a writerow function)
        '''
        tempdicts = []
        for exp in self.expenses_sorted_by_date():
            nd = {}
            nd['date'] = exp.date.strftime('%d.%m.%y').encode('utf-8')
            nd['name'] = exp.participant.name.encode('utf-8')
            nd['description'] = exp.description.encode('utf-8')
            nd['amount'] = str(exp.amount).encode('utf-8')
            tempdicts.append(nd)

        writer = csv.DictWriter(target, ["date", "name", "description", "amount"])
        writer.writerow(dict(date=_('date'), name=_('name'), description=_('description'), amount=_('amount')))
        writer.writerows(tempdicts)


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
    status = Column(Integer(), nullable=True, default=STATUS.OPEN)

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
    def share(self):
        '''the share of this participant in the pot's total sum'''
        return self.share_factor / float(self.pot.share_factor_sum) * self.pot.sum  # attention to python divison! always use float!

    @property
    def result(self):
        '''the amount of money this participant has to get (positive number) or to pay (negative number)'''
        return self.sum - self.share


class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    date = Column(Date(), nullable=False, validate=required, label=_(u'date'))
    description = Column(Unicode(255), nullable=False, validate=required, label=_(u'description'))
    amount = Column(Float(), nullable=False, validate=required, label=_(u'amount'))
    participant_id = Column(Integer(), ForeignKey('participant.id'), label=_(u'participant'))

    def __init__(self, date=None, description='', amount=''):
        self.date = date
        self.description = description
        self.amount = amount


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    date = Column(Date())
    status = Column(Enum(u'open', u'cleared', u'verified', name='state'), default='open')
    amount = Column(Float())
    from_participant_id = Column(Integer(), ForeignKey('participant.id'))
    to_participant_id = Column(Integer(), ForeignKey('participant.id'))

    from_participant = relationship(Participant, primaryjoin='Participant.id == Payment.from_participant_id')
    to_participant = relationship(Participant, primaryjoin='Participant.id == Payment.to_participant_id')

    def __init__(self, from_participant, to_participant, amount):
        self.from_participant = from_participant
        self.to_participant = to_participant
        self.amount = amount
        self.status = u'open'


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
        return sum([p.sum for p in self.participations if p.status == STATUS.OPEN])

    @property
    def result(self):
        '''the amount of money this user has to get (positive number) or to pay (negative number) in total of all his pots'''
        return sum([p.result for p in self.participations if p.status == STATUS.OPEN])

    @property
    def active_participations(self):
        '''return all participations with status OPEN'''
        return [p for p in self.participations if p.status == STATUS.OPEN]

    @property
    def archived_participations(self):
        '''return all archived participations of the user'''
        return [p for p in self.participations if p.status == STATUS.ARCHIVED]


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
