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
        User,
        STATUS)

from moneypot.forms import (
        home_form,
        expense_form,
        invite_form,
        register_form,
        login_form)
from moneypot.utils import dummy_translate as _
from moneypot import mails


@view_config(route_name='home', renderer='templates/home.pt')
def view_home(context, request):
    my_bootstrap.need()    # we need css
    logged_in = authenticated_userid(request)
    if logged_in:
        user = DBSession.query(User).filter_by(username=logged_in).first()
    if not request.POST and logged_in:
        data = {'HomeForm--yourmail': user.email,
                'HomeForm--yourname': user.username
                }
    else:
        data = None
    form = home_form(request.POST or data)
    if request.POST and form.validate():  # if submitted and and valid, create Pot and participant, and then go to pot site
        log.debug("gutes Formular!")
        pot = Pot(form.potname.value)
        DBSession.add(pot)
        participant = Participant(name=form.yourname.value, email=form.yourmail.value)
        pot.participants.append(participant)
        if form .yourmail.value:
            mails.new_pot_mail(request, pot, participant, request.route_url('pot', identifier=participant.identifier))
        if logged_in:
            user.participations.append(participant)
        return HTTPFound(location=request.route_url('pot', identifier=participant.identifier))
    return {'form': form, 'logged_in': logged_in}


@view_config(route_name='register', renderer='templates/register.pt')
def view_register(context, request):
    my_bootstrap.need()    # we need css
    form = register_form(request.POST or None)
    if request.POST and form.validate():  # if submitted and and valid, create Pot and participant, and then go to pot site
        user = User(form.username.value, form.yourmail.value, form.password.value)
        DBSession.add(user)
        return HTTPFound(location=request.route_url('home'))
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
        my_bootstrap.need()
        identifier = request.matchdict['identifier']
        self.logged_in = authenticated_userid(self.request)
        self.participant = DBSession.query(Participant).filter_by(identifier=identifier).one()
        if self.participant is None:
            return
        self.pot = self.participant.pot

        logged_in = authenticated_userid(self.request)
        if logged_in:
            self.user = DBSession.query(User).filter_by(username=logged_in).first()
        else:
            self.user = None

    @view_config(route_name='pot', renderer='templates/pot.pt')
    def pot_view(self):
        if self.pot is None:
            return HTTPNotFound(_('Now pot here'))
        fs = expense_form(DBSession, self.participant)
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
                    user = DBSession.query(User).filter_by(email=invited.email).first()
                    if user is not None:
                        user.participations.append(invited)
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

    @view_config(route_name='take_ownership')
    def take_ownership(self):
        '''
        add this pot (with given identifier) to the users list of "my pots"
        '''
        if self.pot is None:
            return HTTPNotFound(_('Now pot here'))
        if self.user:
            self.participant.user = self.user
            self.request.session.flash(_(u"The pot was added to 'My Pots'"))
        else:
            self.request.session.flash(_(u"Please log in"))
        return HTTPFound(location=self.request.route_url('pot', identifier=self.participant.identifier))

    @view_config(route_name='archive')
    def archive(self):
        '''
        archive this pot for logged in user,
        (it will be shown in archived pots on his list, not under active pots - for the overall sum for the user only active pots account)
        '''
        #to archive pot, set status in participant object to archived
        if self.pot is None:
            return HTTPNotFound(_('Now pot here'))
        #if not logged in, refer user to login page
        if self.user is None:
            return HTTPFound(location=self.request.route_url('login'))
        self.participant.status = STATUS.ARCHIVED
        return HTTPFound(location=self.request.route_url('overview'))


@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    bootstrap_responsive_css.need()
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    form = login_form(request.POST or None)
    if request.POST and form.validate():
        login = form.username.value
        password = form.password.value
        user = DBSession.query(User).filter_by(username=login).first()  # returns user or None
        if user is not None and user.check_password(password):
            headers = remember(request, login)
            request.session.flash(_('Succesfully logged in'))
            return HTTPFound(location=came_from,
                             headers=headers)
        request.session.flash(_(u'Login failed<br />Please try again'))

    return dict(
        came_from=came_from,
        form=form,
        logged_in=authenticated_userid(request),
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

    user = None

    def __init__(self, request):
        '''
        Look for the user document in the database and load it
        '''
        self.request = request
        self.logged_in = authenticated_userid(request)
        if self.logged_in:
            self.user = DBSession.query(User).filter_by(username=self.logged_in).first()

    @view_config(route_name='overview', renderer='templates/overview.pt')
    def overview(self):
        my_bootstrap.need()
        if not self.user:
            return HTTPFound(location=self.request.route_url('login'))
        return dict()
