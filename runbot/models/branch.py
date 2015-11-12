# -*- encoding: utf-8 -*-
from openerp import models, fields, api


class Branch(models.Model):
    _name = 'runbot.branch'

    # Fields
    repo_id = fields.Many2one('runbot.repo', string='Repository',
                              required=True, ondelete='cascade')
    name = fields.Char('Branch', required=True)
    ref_name = fields.Char('Ref name', required=True)
    build_ids = fields.One2many('runbot.build', 'branch_id', string='Builds')
    is_sticky = fields.Boolean(string='Sticky', compute='_compute_is_sticky')

    @api.depends('repo_id', 'repo_id.sticky_branch_ids')
    def _compute_is_sticky(self):
        for branch in self:
            branch.is_sticky = branch in branch.repo_id.sticky_branch_ids
