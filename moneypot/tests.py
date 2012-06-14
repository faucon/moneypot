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

    def test_share_factor_sum(self):
        from moneypot.models import Participant
        pot = self._makeOne()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)
        alice.share_factor = 2
        self.assertEqual(pot.share_factor_sum, 2)
        bob = Participant(name='Bob', email='bob@example.org')
        pot.participants.append(bob)  # with default share factor of one
        self.assertEqual(pot.share_factor_sum, 3)


class TestUser(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def test_password_hash(self):
        '''test if the hashing of passwords works'''
        from moneypot.models import User
        test_user = User(username='test', email='test@example.org', password='test')
        self.session.add(test_user)
        loaded_test_user = self.session.query(User).filter_by(username='test').one()
        self.assertNotEqual(loaded_test_user.password, 'test')  # the password should not be stored in clear text but hashed
        self.assertTrue(loaded_test_user.check_password(u'test'))  # the password can be checked, and works also with unicode
