# -*- encoding: utf-8 -*-
#
#    Copyright Eezee-It
#    Author: Aristobulo Meneses
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
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
