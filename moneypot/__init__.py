from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow, Everyone
from pyramid.session import UnencryptedCookieSessionFactoryConfig
my_session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreetareally')

from moneypot.models import appmaker
from moneypot import models, forms


class RootFactory(object):
    '''
    quasi empty root factory with very simple acl
    '''
    __acl__ = [(Allow, Everyone, 'view'), ]

    def __init__(self, request):
        pass


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    appmaker(engine)
    config = Configurator(settings=settings, session_factory=my_session_factory, root_factory='moneypot.RootFactory')

    if settings['debugmail'] == 'true':
        config.include('pyramid_mailer.testing')
    else:
        config.include('pyramid_mailer')

    auth_policy = AuthTktAuthenticationPolicy(secret='thisshouldbesecret')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(authz_policy)

    config.add_static_view('static', 'moneypot:static', cache_max_age=3600)

    config.add_view('moneypot.views.view_home',
                    name="home",
                    renderer="templates/home.pt")

    config.include('pyramid_formalchemy')
    # Adding the jquery libraries
    config.include('fa.bootstrap')
    # Adding the package specific routes
    config.include('moneypot.routes')

    config.formalchemy_admin("/admin",
                             models=models,
                             forms=forms,
                             session_factory=models.DBSession,
                             view="moneypot.forms.ModelView")

    config.scan()
    return config.make_wsgi_app()
