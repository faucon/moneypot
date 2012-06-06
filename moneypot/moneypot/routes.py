from moneypot import models, forms

def includeme(config):

    try:
        # Example for pyramid_routesalchemy and akhet
        from moneypot.models import MyModel
        config.formalchemy_model("/my_model", package='moneypot',
                                 model='moneypot.models.MyModel',
                                 session_factory=models.DBSession,
                                 view='moneypot.forms.ModelView')
    except ImportError:
        pass
