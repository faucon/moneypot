from formalchemy import forms
from formalchemy import tables
from formalchemy import fields
from formalchemy.fields import Field
from formalchemy import validators
from pyramid.renderers import get_renderer
from fa.bootstrap.views import ModelView as Base
from fa.bootstrap import fanstatic_resources

from moneypot.models import Expense, Participant, User

from moneypot.utils import dummy_translate as _


class FieldSet(forms.FieldSet):
    pass


class Grid(tables.Grid):
    pass


class ModelView(Base):

    def render(self, **kwargs):
        result = super(ModelView, self).render(**kwargs)
        result['main_template'] = get_renderer('moneypot:templates/main_template.pt').implementation()
        result['main'] = get_renderer('fa.bootstrap:templates/admin/master.pt').implementation()
        return result

    def update_resources(self):
        """A hook to add some fanstatic resources"""
        fanstatic_resources.bootstrap.need()


class HomeForm(object):
    '''form for the home view'''

    potname = Field().label(_(u'Pot name')).required()
    yourname = Field().label(_(u'Your name')).required()
    yourmail = Field().label(_(u'Your email')).validate(validators.email)


def home_form(data=None):
    '''
    create Form for creating a Pot with one participant
    '''
    home_fs = FieldSet(HomeForm, data=data)
    return home_fs


def expense_form(DBSession, pot, data=None):
    '''
    create FieldSet for Expense form,
    chosing appropriate participants and configure order of fields
    '''
    expense_fs = FieldSet(Expense, session=DBSession, data=data)
    expense_fs.configure(
            options=[expense_fs.participant.dropdown(options=pot.participants)],
            include=[expense_fs.participant, expense_fs.date, expense_fs.description, expense_fs.amount])
    return expense_fs


def invite_form(DBSession, data=None):
    '''
    create Form to invite new participant
    '''
    invite_fs = FieldSet(Participant, session=DBSession, data=data)
    invite_fs.configure(
            include=[invite_fs.name, invite_fs.email])
    return invite_fs


def login_form(DBSession, data=None):
    '''
    create Form to login user
    '''
    login_fs = FieldSet(User, session=DBSession, data=data)
    login_fs.configure(
            include=[login_fs.username, login_fs.email])
    return login_fs


def passwd_validator(value, field):
    '''validate that two password fields contain the same password'''

    if field.parent.password.value != value:
        raise validators.ValidationError(_(u'Password do not match'))


class RegisterForm(object):
    '''form for the register view'''

    username = Field().label(_(u'Username')).required()
    yourmail = Field().label(_(u'Your email')).required().validate(validators.email)
    password = Field().label(_(u'Password')).required().password()
    password_confirm = Field().label(_(u'Password')).required().password().validate(passwd_validator)


def register_form(data=None):
    '''
    create Form to register User
    '''

    register_fs = FieldSet(RegisterForm, data=data)
    return register_fs
