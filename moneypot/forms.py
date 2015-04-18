'''
Forms with colander/deform
'''
import colander
import deform
import colanderalchemy

import logging
log = logging.getLogger(__name__)

from moneypot.models import Expense, Participant

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('moneypot')


class NewPotSchema(colander.MappingSchema):
    potname = colander.SchemaNode(colander.String(),
                                  title=_(u'Pot name'))
    yourname = colander.SchemaNode(colander.String(),
                                   title=_(u'Your name'))
    yourmail = colander.SchemaNode(colander.String(),
                                   title=_(u'Your email'),
                                   validator=colander.Email())


def home_form():
    return deform.Form(NewPotSchema(), formid='newpot', buttons=(_(u'Create Pot'),))


from formalchemy import forms
from formalchemy import tables
from formalchemy.fields import Field
from formalchemy import validators
from formalchemy import fatypes
from pyramid.renderers import get_renderer
from fa.bootstrap.views import ModelView as Base
from fa.bootstrap import fanstatic_resources

import datetime

from moneypot.renderer import BootstrapDateFieldRenderer

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


def change_password_form(request):
    '''
    create Form to change password
    '''
    #local class, as explained above for HomeForm
    class ChangePasswordForm(object):
        '''form for the login view'''
        old_password = Field().label(_(u'old password')).required().password()
        password = Field().label(_(u'new password')).required().password()
        confirm_password = Field().label(_(u'confirm new password')).required().password().validate(passwd_validator)

    change_fs = FieldSet(ChangePasswordForm, request=request)
    change_fs.configure(
            include=[change_fs.old_password, change_fs.password, change_fs.confirm_password])
    return change_fs


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
