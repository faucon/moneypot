from pyramid.view import view_config
from pyramid.renderers import get_renderer
from fa.bootstrap import fanstatic_resources
from js.bootstrap import bootstrap_responsive_css
from formalchemy import FieldSet

from moneypot.models import DBSession
from moneypot.models import (Pot,
        Participant,
        Expense,
        User,
        Payment)
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
    fs = FieldSet(Expense, session=DBSession)
    fs.configure(options=[fs.participant.dropdown(options=participant.pot.participants)],
            include=[fs.participant, fs.date, fs.description, fs.amount])
    if 'submit' in request.POST:
        ex = Expense()
        fs = FieldSet(ex, session=DBSession, data=request.POST)
        try:
            fs.validate()
            fs.sync()
            participant.expenses.append(ex)
            request.session.flash(_(u'The expense was added'))
        except:
            pass
    return {'form': fs, 'participant': participant, 'pot': participant.pot}
