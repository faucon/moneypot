#coding: utf-8
import unittest

from pyramid import testing
from zope.testbrowser.wsgi import Browser
from bs4 import BeautifulSoup

import transaction


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
        transaction.begin()
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

    def test_result(self):
        '''
        let's assume alice spend 10€, and bob 5€. But alice has share_factor 2, bob has 1.
        Therefore their result should be 0
        '''
        from moneypot.models import Participant
        import datetime
        pot = self._makeOne()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)
        alice.share_factor = 2
        bob = Participant(name='Bob', email='bob@example.org')
        pot.participants.append(bob)  # with default share factor of one
        alice.add_expense(description='Water', amount=10, date=datetime.date.today())
        bob.add_expense(description='Juice', amount=5, date=datetime.date.today())
        self.assertEqual(pot.sum, 15)
        self.assertEqual(pot.share_factor_sum, 3)
        self.assertEqual(alice.sum, 10)
        self.assertEqual(alice.result, 0)
        self.assertEqual(bob.result, 0)

    def test_sorted_expenses(self):
        '''
        sort expenses by date
        '''
        from moneypot.models import Participant
        import datetime
        pot = self._makeOne()
        self.session.add(pot)
        self.session.flush()  # is needed for pot having an id
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)
        #add 2 expenses, one from 2000
        alice.add_expense(description='Water', amount=10, date=datetime.date.today())
        alice.add_expense(description='Juice', amount=5, date=datetime.date(200, 1, 1))
        expense_list = pot.expenses_sorted_by_date()
        self.assertEqual(len(expense_list), 2)
        self.assertEqual(expense_list[0].description, 'Juice')
        self.assertEqual(expense_list[1].description, 'Water')


class TestParticipant(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def test_unicode(self):
        from moneypot.models import Participant
        p = Participant(name="P1", email="p1@example.org")
        self.assertEqual(p.__unicode__(), 'P1 (p1@example.org)')


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


class FunctionalTest(unittest.TestCase):
    '''
    Test the web interface:
        * create a pot
        * add expense
        * invite user
        * invited user adds expense
    test: correct result is shown
    '''

    SITE = 'http://localhost/'

    def setUp(self):
        from moneypot import main
        self.browser = Browser(wsgi_app=main({},
            **{'sqlalchemy.url': "sqlite://",
                'debugmail': 'true',
                'mail.default_sender': 'moneypot@trescher.fr',
                }))

    def invite_bob(self, email=''):
        '''
        start on pot site
        invite bob
        and return link for bob
        '''
        link = self.browser.getLink('Einladen')
        link.click()
        name = self.browser.getControl(name='Participant--name')
        mail = self.browser.getControl(name='Participant--email')
        name.value = 'Bob'
        mail.value = email
        submit = self.browser.getControl(name='submit')
        submit.click()

        #now look for link for bob
        soup = BeautifulSoup(self.browser.contents)
        boblink = soup.find('div', 'well').a['href']  # the link is inside the first "well" (where messages are presented)
        return boblink

    def create_pot(self):
        self.browser.open(self.SITE)
        #Create Pot
        potinput = self.browser.getControl(name="HomeForm--potname")
        nameinput = self.browser.getControl(name="HomeForm--yourname")
        nameinput.value = "Alice"
        potinput.value = "My New Cool Pot"
        submit = self.browser.getControl(name='submit')
        submit.click()

    def add_expense(self, amount="42.0"):
        '''adds an expese'''
        description = self.browser.getControl(name='Expense--description')
        expense = self.browser.getControl(name='Expense--amount')
        description.value = "my very first test expense"
        expense.value = amount

        submit = self.browser.getControl(name='submit')
        submit.click()

    def register(self):
        '''register Alice'''
        username = self.browser.getControl(name='RegisterForm--username')
        email = self.browser.getControl(name='RegisterForm--yourmail')
        password = self.browser.getControl(name='RegisterForm--password')
        password_confirm = self.browser.getControl(name='RegisterForm--password_confirm')

        username.value = 'alice'
        email.value = 'alice@example.org'
        password.value = 'secret'
        password_confirm.value = 'secret'

        submit = self.browser.getControl(name='submit')
        submit.click()

    def login(self):
        '''login Alice'''
        username = self.browser.getControl(name='LoginForm--username')
        password = self.browser.getControl(name='LoginForm--password')

        username.value = 'alice'
        password.value = 'secret'

        submit = self.browser.getControl(name='submit')
        submit.click()

    def test_create_pot(self):
        self.create_pot()

    def test_invite_bob(self):
        self.create_pot()
        boblink = self.invite_bob()
        #try to call this site
        self.browser.open(boblink)

    def test_add_expense(self):
        self.create_pot()
        self.add_expense()
        soup = BeautifulSoup(self.browser.contents)
        expense_text = soup.find('td', text="42.0")
        self.assertIsNotNone(expense_text)

    def test_register_login_logout(self):
        '''
        go to login page, from there follow "register" link.
        register alice and go back to login page
        login
        then try to logout (logout link is only visible if login was successfull)
        '''
        self.browser.open(self.SITE)
        login_link = self.browser.getLink('Login')
        login_link.click()
        register_link = self.browser.getLink('Registration')
        register_link.click()
        self.register()
        login_link = self.browser.getLink('Login')
        login_link.click()
        self.login()
        logout_link = self.browser.getLink('Logout')
        logout_link.click()
