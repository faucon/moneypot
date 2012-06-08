#coding: utf-8
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from moneypot.utils import dummy_translate as _


def new_pot_mail(request, pot, participant, url):
    mailer = get_mailer(request)
    message = Message(subject=_(u'Topf {0} angelegt').format(pot.name),
            recipients=[participant.email, ],
            body=_(u'''
            Hallo {0},

            du hast einen neuen Topf mit dem Namen {1} angelegt.
            Diesen kannst du in Zukunft unter {2} erreichen.

            Viel Spaß mit Moneypot

            Bei Fragen und Anregungen, wende dich an moneypot@trescher.fr
            ''').format(participant.name, pot.name, url)
            )
    mailer.send_immediately(message)


def invite_mail(request, pot, participant, newparticipant, url):
    '''
    send an email to newparticipant, which was invited by participant to participate in pot
    '''
    mailer = get_mailer(request)
    message = Message(subject=_(u'Einladung zum Topf {0}').format(pot.name),
            recipients=[newparticipant.email, ],
            body=_(u'''
            Hallo {0},

            {1} hat dich eingeladen am Topf {2} teilnzunehmen.

            Du kannst den Topf unter {3} erreichen. Dies ist dein persönlicher Link, den du aufheben solltest, solange du den Topf
            benutzen möchtest.

            Viel Spaß mit Moneypot

            Weitere Infos gibt's unter www.trescher.fr

            Bei Fragen und Anregungen, wende dich an moneypot@trescher.fr
            ''').format(newparticipant.name, participant.name, pot.name, url)
            )
    mailer.send_immediately(message)
