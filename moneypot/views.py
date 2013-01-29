# coding: utf-8
from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import NotFound
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
from moneypot import mails
from pyramid.i18n import TranslationStringFactory, get_locale_name, get_localizer

_ = TranslationStringFactory('moneypot')


@view_config(route_name='home', renderer='templates/home.pt')
def view_home(context, request):
    my_bootstrap.need()    # we need css
    logged_in = authenticated_userid(request)
    log.debug("Locale: " + get_locale_name(request))
    if logged_in:
        user = DBSession.query(User).filter_by(username=logged_in).first()
    if not request.POST and logged_in:
        data = {'HomeForm--yourmail': user.email,
                'HomeForm--yourname': user.username
                }
    else:
        data = None
    form = home_form(request, data=request.POST or data)
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

    log.debug("Form: %s with model %s", str(id(form)), str(form.model))
    log.debug("Field: %s", str(id(form.potname)))
    log.debug("Form has errors? %s", str(form.errors))
    return {'form': form, 'logged_in': logged_in}


@view_config(route_name='register', renderer='templates/register.pt')
def view_register(context, request):
    my_bootstrap.need()    # we need css
    form = register_form(request)
    if request.POST and form.validate():  # if submitted and and valid, create user
        existing_user = DBSession.query(User).filter_by(username=form.username.value).first()  # check for eyisting user with this name, returns existing user or None
        if not existing_user:
            user = User(form.username.value, form.yourmail.value, form.password.value)
            DBSession.add(user)
            return HTTPFound(location=request.route_url('home'))
        else:
            request.session.flash(_(u'username already taken. Please choose another username.'))
    return {'form': form, 'logged_in': authenticated_userid(request)}


class PotView(object):
    '''
    this encapsulates the views which act on a dedicated pot
    '''

    def __init__(self, request):
        '''
        Look for the pot document in the database, load is and create pot object and user
        '''
        #save request for later use
        self.request = request

        #all the potviews need bootstrap
        my_bootstrap.need()

        #find the pot
        identifier = request.matchdict['identifier']
        self.participant = DBSession.query(Participant).filter_by(identifier=identifier).first()
        if self.participant is None:
            raise NotFound(_(u'No Pot found'))
        self.pot = self.participant.pot
        if self.pot is None:
            raise NotFound(_(u'No Pot found'))

        #check for logged in user
        self.logged_in = authenticated_userid(self.request)
        logged_in = authenticated_userid(self.request)
        if logged_in:
            self.user = DBSession.query(User).filter_by(username=logged_in).first()
        else:
            self.user = None

        #redirect to pot-home
        self.redirect_to_pot = HTTPFound(location=self.request.route_url('pot', identifier=self.participant.identifier))

    @view_config(route_name='pot', renderer='templates/pot.pt')
    def pot_view(self):
        fs = expense_form(DBSession, self.participant, self.request)
        if 'submit' in self.request.POST:
            log.debug('Try to save a new expense, called from participant {0} {1}'.format(self.participant, self.participant.identifier))
            ex = Expense()
            fs = fs.bind(ex)
            fs.data = self.request.POST
            if fs.validate():
                fs.sync()
                expensing_participant = DBSession.query(Participant).get(ex.participant_id)
                expensing_participant.expenses.append(ex)
                self.request.session.flash(_(u'The expense of {0} € was added.').format(ex.amount))
                return self.redirect_to_pot
            else:
                pass
                #do nothing and return form with error messages
        return {'form': fs, 'participant': self.participant, 'pot': self.pot}

    @view_config(route_name='invite_participant', renderer='templates/invite.pt')
    def invite(self):
        '''
        This view shows an form for inviting someone
        '''
        fs = invite_form(DBSession, self.request)
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
                return self.redirect_to_pot
            else:
                pass
                #do nothing and return form with error messages
        return {'form': fs, 'participant': self.participant, 'pot': self.pot}

    @view_config(route_name='change_factor')
    def change_factor(self):
        '''
        change the share factor of one of the participants
        '''
        #get values from request
        participant_id = self.request.matchdict['participant_to_change_id']
        factor = self.request.matchdict['new_factor']
        #change it to integer:
        try:
            factor = int(factor)
        except ValueError:
            #error message
            #(should never occur from ui, only from improper http-requests
            self.request.session.flash(_(u"Don't do this, not an integer"))
            return self.redirect_to_pot

        #load participant
        changed_participant = DBSession.query(Participant).filter_by(identifier=participant_id).one()
        #make sure participant exists and belongs to this pot!
        if (not changed_participant) or (not changed_participant.pot == self.pot):
            #error message
            #(should never occur from ui, only from improper http-requests
            self.request.session.flash(_(u"Don't do this"))
            return self.redirect_to_pot

        #make sure that the new share_factor_sum is != 0 (someone has to pay!)
        new_factorsum = self.pot.share_factor_sum - changed_participant.share_factor + factor
        if new_factorsum == 0:
            #error message:
            self.request.session.flash(_(u'The sum of all factors may not be 0'))
            return self.redirect_to_pot

        #if all checks were successfull, now do the change:
        changed_participant.share_factor = factor
        self.request.session.flash(_(u'The share factor for {0} was changed to {1}'.format(str(changed_participant), str(factor))))
        return self.redirect_to_pot

    @view_config(route_name='remove_expense')
    def remove_expense(self):
        '''
        This view removes an expense
        '''
        id_to_remove = self.request.matchdict['id_to_remove']
        expense = DBSession.query(Expense).get(id_to_remove)
        DBSession.delete(expense)
        self.request.session.flash(_(u'The expense of {0} € got deleted').format(expense.amount))
        return self.redirect_to_pot

    @view_config(route_name='remove_participant', renderer='templates/question.pt')
    def remove_participant(self):
        '''
        This view removes an participant,
        it shows a warning if this participant already added expenses
        '''
        id_participant_to_remove = self.request.matchdict['id_participant_to_remove']
        participant = DBSession.query(Participant).get(id_participant_to_remove)

        #check if a participant was found
        if None == participant:
            self.request.session.flash(_(u"An error occured while searching the participant"))
            return self.redirect_to_pot

        #check if participant belongs to this pot
        # should not occur from ui, but only from "hackish" calls
        if participant.pot != self.pot:
            self.request.session.flash(_(u"This is not allowed!"))
            return self.redirect_to_pot
        #now everything should be fine

        # if participant has no expenses, delete him right away,
        # if he has expenses, wait for "submit" which means that the user confirmed his choice
        if not participant.expenses or 'submit' in self.request.POST:
            DBSession.delete(participant)
            self.request.session.flash(_(u'The participant {0} and all his expenses got deleted').format(participant.name))
            return self.redirect_to_pot
        else:
            question = {
                'title': _(u'Delete {0}?').format(participant.name),
                'message': _(u'The participant {0} already entered some expenses. These would be lost. Are you sure you want to proceed?').format(participant.name)
            }
            log.debug('return a question')
            return {'question': question, }

    @view_config(route_name='take_ownership')
    def take_ownership(self):
        '''
        add this pot (with given identifier) to the users list of "my pots"
        '''
        if self.user:
            self.participant.user = self.user
            self.request.session.flash(_(u"The pot was added to 'My Pots'"))
        else:
            self.request.session.flash(_(u"Please log in"))
        return self.redirect_to_pot

    @view_config(route_name='archive')
    def archive(self):
        '''
        archive this pot for logged in user,
        (it will be shown in archived pots on his list, not under active pots - for the overall sum for the user only active pots account)
        '''
        #to archive pot, set status in participant object to archived
        #if not logged in, refer user to login page
        if self.user is None:
            return HTTPFound(location=self.request.route_url('login'))
        self.participant.status = STATUS.ARCHIVED
        return HTTPFound(location=self.request.route_url('overview'))

    @view_config(route_name='unarchive')
    def unarchive(self):
        '''
        unarchive this pot for logged in user,
        move it again to "open" pots
        '''
        #to archive pot, set status in participant object to archived
        #if not logged in, refer user to login page
        if self.user is None:
            return HTTPFound(location=self.request.route_url('login'))
        self.participant.status = STATUS.OPEN
        return HTTPFound(location=self.request.route_url('overview'))


@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    bootstrap_responsive_css.need()
    trans = get_localizer(request).translate
    form = login_form(request)
    if request.POST and form.validate():
        login = form.username.value
        password = form.password.value
        user = DBSession.query(User).filter_by(username=login).first()  # returns user or None
        if user is not None and user.check_password(password):
            headers = remember(request, login)
            request.session.flash(trans(_('Succesfully logged in')))
            return HTTPFound(location=request.route_url('overview'),
                             headers=headers)
        request.session.flash(trans(_(u'Login failed<br />Please try again')))

    return dict(
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
