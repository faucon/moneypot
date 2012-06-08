from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from fa.bootstrap import fanstatic_resources
from js.bootstrap import bootstrap_responsive_css

import logging
log = logging.getLogger(__name__)

from moneypot.models import DBSession
from moneypot.models import (
        Participant,
        Expense,)
from moneypot.forms import (
        expense_form,
        invite_form)
from moneypot.utils import dummy_translate as _
from moneypot import mails


def view_home(context, request):
    fanstatic_resources.bootstrap.need()
    main_template = get_renderer('moneypot:templates/main_template.pt').implementation()
    return {'main_template': main_template, 'project': 'moneypot'}


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
