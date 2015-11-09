# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class Build(models.Model):
    _name = 'runbot.build'
    _rec_name = 'commit'

    # Fields
    commit = fields.Char(string='Commit', required=True)
    state = fields.Selection([
        ('creation', _('Creation')),
        ('running', _('Running')),
        ('killed', _('Killed')),
        ('stopped', _('Stopped')), ], string='Status', default='creation')
    last_state_since = fields.Datetime(
        string='Since', default=fields.Datetime.now())
    branch_id = fields.Many2one(
        'runbot.branch', string='Branch', required=True)
    repo_id = fields.Many2one(
        'runbot.repo', string='Repository', related='branch_id.repo_id',
        store=True)
    pid = fields.Integer(string='Process ID')
    port = fields.Integer(string='Port')

    @api.multi
    def kill(self):
        _logger.info('Killing build: %s-%s' %
                     (self.commit, self.branch_id.name))
        return

    @api.multi
    def start(self):
        """
        Run odoo build
        :return: boolean
        """
        self.ensure_one()
        _logger.info('Starting build: %s-%s' %
                     (self.commit, self.branch_id.name))
        return True

    @api.multi
    def prepare(self):
        """
        Prepare build instance, by default it will create a virtualenv,
        install from requirements.txt and generate a clean database
        :return:
        """
        self.ensure_one()
        _logger.info('Preparing build: %s-%s' %
                     (self.commit, self.branch_id.name))
        return True

    @api.multi
    def log(self, n=50):
        """
        Get build logfile
        :param n: number of lines
        :return: last n lines of logfile
        """
        self.ensure_one()
        return
