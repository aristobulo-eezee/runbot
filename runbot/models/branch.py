# -*- encoding: utf-8 -*-
from openerp import models, fields


class Branch(models.Model):
    _name = 'runbot.branch'

    # Fields
    repo_id = fields.Many2one('runbot.repo', string='Repository',
                              required=True, ondelete='cascade')
    name = fields.Char('Branch', required=True)
    ref_name = fields.Char('Ref name', required=True)
