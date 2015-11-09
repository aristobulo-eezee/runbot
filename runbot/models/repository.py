# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _


class Repository(models.Model):
    _name = 'runbot.repo'

    # Fields
    active = fields.Boolean('Active', default=True)
    alias = fields.Char('Alias')
    name = fields.Char('Repository', required=True)
    published = fields.Boolean('Available on website', default=False)
    git_host = fields.Selection([
        ('local', _('Local')), ], string='Hosting', required=True,
        default='local',
        help='Provider where git repository is hosted. Local means git '
             'repository is located on the same filesystem as runbot.')
    branch_ids = fields.One2many('runbot.branch', 'repo_id', string='Branches')
    sticky_branch_ids = fields.Many2many(
        'runbot.branch', 'rel_repo_sticky_branch', 'repo_id', 'branch_id',
        string='Sticky branches')

    @api.multi
    def update_branches(self):
        pass

    @api.multi
    def repo_publish_button(self):
        self.write({'published': True})
