from pyramid.renderers import get_renderer
from fa.bootstrap import fanstatic_resources


def view_home(context, request):
    fanstatic_resources.bootstrap.need()
    main_template = get_renderer('moneypot:templates/main_template.pt').implementation()
    return {'main_template': main_template, 'project':'moneypot'}
