from pyramid.view import view_config
from pyramid.renderers import get_renderer
from fa.bootstrap import fanstatic_resources
from js.bootstrap import bootstrap_responsive_css

import logging
log = logging.getLogger(__name__)

from moneypot.models import DBSession
from moneypot.models import (
        Participant,
        Expense,)
from moneypot.forms import (
        expense_form,)
from moneypot.utils import dummy_translate as _


def view_home(context, request):
    fanstatic_resources.bootstrap.need()
    main_template = get_renderer('moneypot:templates/main_template.pt').implementation()
    return {'main_template': main_template, 'project': 'moneypot'}


@view_config(route_name='pot', renderer='templates/pot.pt')
def pot_view(context, request):
    bootstrap_responsive_css.need()
    identifier = request.matchdict['identifier']
    participant = DBSession.query(Participant).filter_by(identifier=identifier).one()
    fs = expense_form(DBSession, participant.pot)
    if 'submit' in request.POST:
        log.debug('Try to save a new expense, called from participant {0} {1}'.format(participant, identifier))
        ex = Expense()
        fs = fs.bind(ex)
        fs.data = request.POST
        if fs.validate():
            fs.sync()
            participant.expenses.append(ex)
            request.session.flash(_(u'The expense was added'))
        else:
            pass
            #do nothing and return form with error messages
    return {'form': fs, 'participant': participant, 'pot': participant.pot}
