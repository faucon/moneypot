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


def _make_a_pot():
    from moneypot.models import Pot
    return Pot('testpot')


class TestPot(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def test_sum(self):
        from moneypot.models import Participant
        import datetime
        pot = _make_a_pot()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)
        transaction.begin()
        alice.add_expense(description='Water', amount=10, date=datetime.date.today())
        self.assertEqual(pot.sum, 10)

    def test_share_factor_sum(self):
        from moneypot.models import Participant
        pot = _make_a_pot()
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
        pot = _make_a_pot()
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
        pot = _make_a_pot()
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


class TestSolver(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def test2paricipantsolver(self):
        '''
        create one pot, two participants, one expense
        solve this: second participant must pay this amount
        '''
        from moneypot.models import Participant
        import datetime
        pot = _make_a_pot()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)  # share factor defaults to 1
        bob = Participant(name='Bob', email='bob@example.org')
        pot.participants.append(bob)  # with default share factor of 1
        alice.add_expense(description='Water', amount=10, date=datetime.date.today())
        #close this pot and create open payment to balance the payments
        #alice paid 10 Euro, bob has to pay 5 euro to alice
        payments = pot.close_and_solve()
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.from_participant, bob)
        self.assertEqual(payment.to_participant, alice)
        self.assertEqual(payment.amount, 5)
        self.assertEqual(payment.status, 'open')

    def test3paricipantsolver(self):
        '''
        create one pot, 3 participants, one expense
        solve this: the two others have to pay 1/3 of the total expense.
        '''
        from moneypot.models import Participant
        import datetime
        pot = _make_a_pot()
        alice = Participant(name='Alice', email='alice@example.org')
        pot.participants.append(alice)  # share factor defaults to 1
        bob = Participant(name='Bob', email='bob@example.org')
        pot.participants.append(bob)  # with default share factor of 1
        charlie = Participant(name='charlie', email='charlie@example.org')
        pot.participants.append(charlie)

        alice.add_expense(description='Water', amount=3, date=datetime.date.today())
        #close this pot and create open payment to balance the payments
        #alice paid 3 Euro, bob has to pay 1 euro to alice and charlie too
        #TODO: there may be problems with half-cent payments... what to do about this?
        payments = pot.close_and_solve()
        self.assertEqual(len(payments), 2)
        payment = payments[0]
        self.assertEqual(payment.from_participant, bob)
        self.assertEqual(payment.to_participant, alice)
        self.assertEqual(payment.amount, 1)
        self.assertEqual(payment.status, 'open')
        payment = payments[1]
        self.assertEqual(payment.from_participant, charlie)
        self.assertEqual(payment.to_participant, alice)
        self.assertEqual(payment.amount, 1)
        self.assertEqual(payment.status, 'open')


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

    def tearDown(self):
        testing.tearDown()

    def invite_bob(self, email=''):
        '''
        start on pot site
        invite bob
        and return link for bob
        '''
        link = self.browser.getLink('Invite')
        link.click()
        name = self.browser.getControl(name='Participant--name')
        mail = self.browser.getControl(name='Participant--email')
        name.value = 'Bob'
        mail.value = email
        submit = self.browser.getControl(name='submit')
        submit.click()

        #now look for link for bob
        soup = BeautifulSoup(self.browser.contents)
        boblink = soup.find('div', 'alert').a['href']  # the link is inside the first "alert" (where messages are presented)
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

    def remove_expense(self):
        pass

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

    def login(self, username='alice', password='secret'):
        '''login Alice'''
        username_control = self.browser.getControl(name='LoginForm--username')
        password_control = self.browser.getControl(name='LoginForm--password')

        username_control.value = username
        password_control.value = password

        submit = self.browser.getControl(name='submit')
        submit.click()

    def test_create_pot(self):
        self.create_pot()

    def test_invite_bob(self):
        self.create_pot()
        boblink = self.invite_bob('test@example.org')
        #try to call this site
        self.browser.open(boblink)
        #try to remove someone
        link = self.browser.getLink(url="remove")
        link.click()

    def test_add_expense(self):
        self.create_pot()
        self.add_expense()
        soup = BeautifulSoup(self.browser.contents)
        expense_text = soup.find('td', text="42.00")
        self.assertIsNotNone(expense_text)

    def test_remove_expense(self):
        self.create_pot()
        self.add_expense()
        soup = BeautifulSoup(self.browser.contents)
        expense_text = soup.find('td', text="42.00")
        self.assertIsNotNone(expense_text)
        self.remove_expense()
        amount_text = soup.find('td', text="0.00")
        self.assertIsNotNone(amount_text)

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

    def test_change_password(self):
        '''
        go to login page, from there follow "register" link.
        register alice and go back to login page
        login
        change alices password
        logout and
        login with new password
        '''
        self.browser.open(self.SITE)
        #go to login page
        login_link = self.browser.getLink('Login')
        login_link.click()
        #follow registration link
        register_link = self.browser.getLink('Registration')
        register_link.click()
        #register alice with password secret
        self.register()
        #log her in
        login_link = self.browser.getLink('Login')
        login_link.click()
        self.login()

        #try to change her password
        change_password_link = self.browser.getLink('Change Password')
        change_password_link.click()

        old_password = self.browser.getControl(name='ChangePasswordForm--old_password')
        new_password = self.browser.getControl(name='ChangePasswordForm--password')
        confirm_password = self.browser.getControl(name='ChangePasswordForm--confirm_password')

        old_password.value = 'secret'
        new_password.value = 'newsecret'
        confirm_password.value = 'newsecret'
        submit = self.browser.getControl(name='submit')
        submit.click()

        self.assertIn('changed password', self.browser.contents)

        #logout
        logout_link = self.browser.getLink('Logout')
        logout_link.click()

        #login with new password
        login_link = self.browser.getLink('Login')
        login_link.click()
        self.login(password='newsecret')
        #try if login was successfull: logout link is only visible when logged in
        logout_link = self.browser.getLink('Logout')

        #change back
        change_password_link = self.browser.getLink('Change Password')
        change_password_link.click()

        old_password = self.browser.getControl(name='ChangePasswordForm--old_password')
        new_password = self.browser.getControl(name='ChangePasswordForm--password')
        confirm_password = self.browser.getControl(name='ChangePasswordForm--confirm_password')

        old_password.value = 'newsecret'
        new_password.value = 'secret'
        confirm_password.value = 'secret'
        submit = self.browser.getControl(name='submit')
        submit.click()

        self.assertIn('changed password', self.browser.contents)

    def test_overview(self):
        '''
        log in as registered user, check in the overview page for newly created pots
        '''
        self.test_register_login_logout()
        login_link = self.browser.getLink('Login')
        login_link.click()
        self.login()
        #now we should directly be redirected to overview page
        self.assertIn('Overview', self.browser.contents)
        self.assertIn('alice', self.browser.contents)

        #now create new pot
        new_pot_link = self.browser.getLink('New Pot')
        new_pot_link.click()
        #name and email should be set automatically
        potname = self.browser.getControl(name='HomeForm--potname')
        potname.value = 'testpot'
        submit = self.browser.getControl(name='submit')
        submit.click()

        #go to overview
        overview_link = self.browser.getLink('Overview')
        overview_link.click()

        self.assertIn('testpot', self.browser.contents)

        archive_link = self.browser.getLink(url='archive')
        archive_link.click()

        #need to check that the pot was moved in the archive
        #just try to unarchive it

        unarchive_link = self.browser.getLink(url='unarchive')
        unarchive_link.click()

        #TODO: check somehow it was really unarchived.
