from moneypot import models, forms

def includeme(config):

    try:
        config.formalchemy_model("/pot", package='moneypot',
                                 model='moneypot.models.Pot',
                                 session_factory=models.DBSession,
                                 view='moneypot.forms.ModelView')
    except ImportError:
        pass
