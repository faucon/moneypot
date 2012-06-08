from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from moneypot.models import appmaker
from moneypot import models, forms


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    appmaker(engine)
    config = Configurator(settings=settings)
    config.add_static_view('static', 'moneypot:static', cache_max_age=3600)
    config.add_view('moneypot.views.view_home',
                    name="",
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
