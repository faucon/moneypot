import unittest

from pyramid import testing


def _initTestingDB():
    from sqlalchemy import create_engine
    from moneypot.models import initialize_sql
    session = initialize_sql(create_engine('sqlite://'))
    return session


class TestPot(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def _makeOne(self):
        from moneypot.models import Pot
        return Pot('testpot')

    def test_sum(self):
        from moneypot.models import Participant
        import datetime
        pot = self._makeOne()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)
        alice.add_expense(description='Water', amount=10, date=datetime.date.today())
        self.assertEqual(pot.sum, 10)
