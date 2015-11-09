# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _


class Repository(models.Model):
    _name = 'runbot.repository'

    # Fields
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Repository', required=True)
    published = fields.Boolean('Available on website', default=False)
