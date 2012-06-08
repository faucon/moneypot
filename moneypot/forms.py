from formalchemy import forms
from formalchemy import tables
from pyramid.renderers import get_renderer
from fa.bootstrap.views import ModelView as Base
from fa.bootstrap import fanstatic_resources

from moneypot.models import Expense


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
