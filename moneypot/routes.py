def includeme(config):
    config.add_route('pot', '/pot/{identifier}/')
    config.add_route('invite_participant', '/pot/{identifier}/invite/')
    config.add_route('remove_participant', '/pot/{identifier}/remove/{identifier_to_remove}')
    config.add_route('remove_expense', '/pot/{identifier}/remove_expense/{id_to_remove}')
    config.add_route('expenses_download', '/pot/{identifier}/download.csv')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
