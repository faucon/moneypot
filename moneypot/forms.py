'''
FormAlchemy Forms can translate labels of fields, but for this to work they need to know the request!
'''
from formalchemy import forms
from formalchemy import tables
from formalchemy.fields import Field
from formalchemy import validators
from formalchemy import fatypes
from pyramid.renderers import get_renderer
from fa.bootstrap.views import ModelView as Base
from fa.bootstrap import fanstatic_resources

import datetime

import logging
log = logging.getLogger(__name__)

from moneypot.models import Expense, Participant

from moneypot.renderer import BootstrapDateFieldRenderer
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('moneypot')


class FieldSet(forms.FieldSet):

    def __init__(self, *args, **kwargs):
        '''
        change default renderer for DateType
        '''
        super(FieldSet, self).__init__(*args, **kwargs)
        self.default_renderers[fatypes.Date] = BootstrapDateFieldRenderer

    def validate(self, *args, **kwargs):
        '''log all validate calls for debug reasons'''
        log.debug('validate called on %s', str(self))
        return super(FieldSet, self).validate(*args, **kwargs)


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


def home_form(request, data=None):
    '''
    create Form for creating a Pot with one participant
    '''

    #this class is local, to fix a problem with persistent instances if the fields,
    #so not only new instances are created (with the same instances of Fields every time for all form instances)
    #but the whole class is created when this function is called
    class HomeForm(object):
        '''form for the home view'''

        potname = Field().label(_(u'Pot name')).required()
        yourname = Field().label(_(u'Your name')).required()
        yourmail = Field().label(_(u'Your email')).validate(validators.email)

    home_fs = FieldSet(HomeForm, data=data, request=request)
    return home_fs


def expense_form(DBSession, participant, request, data=None):
    '''
    create FieldSet for Expense form,
    chosing appropriate participants and configure order of fields
    '''
    if data is None:
        tod = datetime.datetime.today()
        data = {'Expense--date__year': str(tod.year),
                'Expense--date__month': str(tod.month),
                'Expense--date__day': str(tod.day),
                'Expense--participant_id': participant.id}
    expense_fs = FieldSet(Expense, session=DBSession, data=data, request=request)
    expense_fs.configure(
            options=[expense_fs.participant.dropdown(options=participant.pot.participants)],
            include=[expense_fs.participant, expense_fs.date, expense_fs.description, expense_fs.amount])
    return expense_fs


def invite_form(DBSession, request):
    '''
    create Form to invite new participant
    '''
    invite_fs = FieldSet(Participant, session=DBSession, request=request)
    invite_fs.configure(
            include=[invite_fs.name, invite_fs.email])
    return invite_fs


def login_form(request):
    '''
    create Form to login user
    '''
    #local class, as explained above for HomeForm
    class LoginForm(object):
        '''form for the login view'''
        username = Field().label(_(u'Username')).required()
        password = Field().label(_(u'Password')).required().password()

    login_fs = FieldSet(LoginForm, request=request)
    login_fs.configure(
            include=[login_fs.username, login_fs.password])
    return login_fs


def passwd_validator(value, field):
    '''validate that two password fields contain the same password'''

    if field.parent.password.value != value:
        raise validators.ValidationError(_(u'Password do not match'))


def register_form(request):
    '''
    create Form to register User
    '''
    #local class, as explained for homeForm
    class RegisterForm(object):
        '''form for the register view'''

        username = Field().label(_(u'Username')).required()
        yourmail = Field().label(_(u'Your email')).required().validate(validators.email)
        password = Field().label(_(u'Password')).required().password()
        password_confirm = Field().label(_(u'Confirm password')).required().password().validate(passwd_validator)

    register_fs = FieldSet(RegisterForm, request=request)
    register_fs.configure(
            include=[register_fs.username, register_fs.yourmail, register_fs.password, register_fs.password_confirm])
    return register_fs


class Question(object):
    '''
    a question object

    does nothing than transport a message
    '''

    def __init__(self, title, message):
        self.title = title
        self.message = message
