# -*- encoding: utf-8 -*-
from openerp import models, fields


class RepoTag(models.Model):
    _name = 'runbot.repo.tag'

    # Fields
    name = fields.Char('Tag')
    repo_id = fields.Many2one('runbot.repo', string='Repository')
