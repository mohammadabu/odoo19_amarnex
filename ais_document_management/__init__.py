# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizards

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='19.0':
        raise UserError('This module support Odoo 19.0, found {}.'.format(server_serie))
    return True