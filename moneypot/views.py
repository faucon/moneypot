from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import forget, remember, authenticated_userid
from js.bootstrap import bootstrap_responsive_css, bootstrap_js
from fanstatic import Group

my_bootstrap = Group([bootstrap_responsive_css, bootstrap_js])

import logging
log = logging.getLogger(__name__)

from moneypot.models import DBSession
from moneypot.models import (
        Pot,
        Participant,
        Expense,
        User)

from moneypot.forms import (
        home_form,
        expense_form,
        invite_form)
from moneypot.utils import dummy_translate as _
from moneypot import mails


@view_config(route_name='home', renderer='templates/home.pt')
def view_home(context, request):
    my_bootstrap.need()    # we need css
    form = home_form(request.POST or None)
    if request.POST and form.validate():  # if submitted and and valid, create Pot and participant, and then go to pot site
        log.debug("gutes Formular!")
        pot = Pot(form.potname.value)
        DBSession.add(pot)
        participant = Participant(name=form.yourname.value, email=form.yourmail.value)
        pot.participants.append(participant)
        return HTTPFound(location=request.route_url('pot', identifier=participant.identifier))
    return {'form': form, 'logged_in': authenticated_userid(request)}


class PotView(object):
    '''
    this encapsulates the views which act on a dedicated pot
    '''

    #variables of this class
    pot = None
    participant = None
    request = None

    def __init__(self, request):
        '''
        Look for the pot document in the database, load is and create pot object and user
        '''
        self.request = request
        bootstrap_responsive_css.need()
        identifier = request.matchdict['identifier']
        self.participant = DBSession.query(Participant).filter_by(identifier=identifier).one()
        if self.participant is None:
            return
        self.pot = self.participant.pot

    @view_config(route_name='pot', renderer='templates/pot.pt')
    def pot_view(self):
        if self.pot is None:
            return HTTPNotFound(_('Hier ist kein Topf'))
        fs = expense_form(DBSession, self.participant.pot)
        if 'submit' in self.request.POST:
            log.debug('Try to save a new expense, called from participant {0} {1}'.format(self.participant, self.participant.identifier))
            ex = Expense()
            fs = fs.bind(ex)
            fs.data = self.request.POST
            if fs.validate():
                fs.sync()
                expensing_participant = DBSession.query(Participant).get(ex.participant_id)
                expensing_participant.expenses.append(ex)
                self.request.session.flash(_(u'The expense was added'))
            else:
                pass
                #do nothing and return form with error messages
        return {'form': fs, 'participant': self.participant, 'pot': self.pot}

    @view_config(route_name='invite_participant', renderer='templates/invite.pt')
    def invite(self):
        '''
        This view shows an form for inviting someone
        '''
        if self.pot is None:
            return HTTPNotFound(_('Hier ist kein Topf'))
        fs = invite_form(DBSession)
        if 'submit' in self.request.POST:
            log.debug('Try to invite a new participant, called from participant {0} {1}'.format(self.participant, self.participant.identifier))
            invited = Participant()
            fs = fs.bind(invited)
            fs.data = self.request.POST
            if fs.validate():
                fs.sync()
                self.pot.participants.append(invited)
                newurl = self.request.route_url('pot', identifier=invited.identifier)
                if invited.email:
                    mails.invite_mail(self.request, self.pot, self.participant, invited, newurl)
                self.request.session.flash(_(u'''{0} wurde eingeladen. Wenn du eine Mailadresse
                angegeben hast, wird ihm der Link per Mail geschickt. Sonst musst du ihm
                folgenden Link zukommen lassen: <a href={1}>{1}</a>'''.format(invited.name, newurl)))
                return HTTPFound(location=self.request.route_url('pot', identifier=self.participant.identifier))
            else:
                pass
                #do nothing and return form with error messages
        return {'form': fs, 'participant': self.participant, 'pot': self.pot}

    @view_config(route_name='remove_expense')
    def remove_expense(self):
        '''
        This view removes an expense
        '''
        if self.pot is None:
            return HTTPNotFound(_('Hier ist kein Topf'))
        id_to_remove = self.request.matchdict['id_to_remove']
        expense = DBSession.query(Expense).get(id_to_remove)
        DBSession.delete(expense)
        self.request.session.flash(_(u'Die Ausgabe wurde entfernt'))
        return HTTPFound(location=self.request.route_url('pot', identifier=self.participant.identifier))


@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    bootstrap_responsive_css.need()
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    login = ''
    password = ''
    if 'submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        user = DBSession.query(User).filter_by(username=login).first()  # returns user or None
        if user is not None and user.check_password(password):
            headers = remember(request, login)
            return HTTPFound(location=came_from,
                             headers=headers)
        request.session.flash(_(u'Login failed<br />Please try again'))

    return dict(
        came_from=came_from,
        login=login,
        logged_in=authenticated_userid(request),
        password=password,
        )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('home'),
                     headers=headers)


class UserView(object):
    '''
    These class contains all views concerning user-centric actions
    '''

    def __init__(self, request):
        '''
        Look for the user document in the database and load it
        '''
        self.request = request
        self.loggedin = authenticated_userid(request)
