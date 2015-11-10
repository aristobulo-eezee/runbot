# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _

import logging
import subprocess
import os
import shutil
import socket
import virtualenv

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
        'runbot.branch', string='Branch', required=True, ondelete='cascade')
    repo_id = fields.Many2one(
        'runbot.repo', string='Repository', related='branch_id.repo_id',
        store=True)
    pid = fields.Integer(string='Process ID')
    port = fields.Integer(string='Port')
    lp_port = fields.Integer(string='Longpolling Port')

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
        # 1. Create virtualenv
        env_dir = '%sbuild/%s-%s' % (self.repo_id.root(), self.branch_id.name,
                                     self.commit)
        parts_dir = '%s/parts' % env_dir
        custom_dir = '%s/custom' % parts_dir
        odoo_dir = '%s/odoo' % parts_dir
        if not os.path.exists(env_dir):
            virtualenv.create_environment(env_dir)
        # 2. Create parts dir
        if not os.path.exists(parts_dir):
            os.makedirs(parts_dir)
        else:
            shutil.rmtree('%s/*' % parts_dir, ignore_errors=True)
        # 3. Clone sources
        _logger.info('Cloning %s' % self.branch_id.name)
        self.repo_id.clone(branch=self.branch_id.name, to_path=custom_dir)
        _logger.info('Cloning odoo')
        odoo_repo = self.env['runbot.repo'].search([
            ('odoo_repo', '=', True)], limit=1)
        # TODO: Read runbot.config from repository to set odoo version
        odoo_repo.clone(branch='8.0', to_path=odoo_dir)
        # 4. Install python packages
        _logger.info('Installing odoo dependencies')
        venv = os.environ.copy()
        venv['PATH'] += '/Library/PostgreSQL/9.3/bin/:'
        # Fix from https://github.com/gevent/gevent/issues/656
        venv['CFLAGS'] = '-std=c99'
        pip_odoo = subprocess.Popen([
            '%s/bin/pip' % env_dir, 'install', '-r',
            '%s/requirements.txt' % odoo_dir], env=venv)
        pip_odoo.wait()
        _logger.info('Installing custom dependencies')
        pip_custom = subprocess.Popen([
            '%s/bin/pip' % env_dir, 'install', '-r',
            '%s/requirements.txt' % custom_dir])
        pip_custom.wait()
        _logger.info('Get open ports for odoo and longpolling.')
        odoo_port = self.get_open_port()
        lp_port = self.get_open_port()
        _logger.info('Found %s and %s.' % (odoo_port, lp_port))
        _logger.info('Starting odoo server.')
        odoo_server = subprocess.Popen([
            '%s/bin/python' % env_dir, '%s/openerp-server' % odoo_dir,
            '-r', 'odoo',
            '--addons-path=%s/addons,%s' % (odoo_dir, custom_dir),
            '--xmlrpc-port=%s' % odoo_port, '--longpolling-port=%s' % lp_port],
            env=venv)
        self.write({
            'pid': odoo_server.pid,
            'port': odoo_port,
            'lp_port': lp_port,
        })
        return True

    def get_open_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    @api.multi
    def log(self, n=50):
        """
        Get build logfile
        :param n: number of lines
        :return: last n lines of logfile
        """
        self.ensure_one()
        return

    def unlink(self, cr, uid, ids, context=None):
        builds = self.browse(cr, uid, ids, context=context)
        for build in builds:
            build_path = '%sbuild/%s-%s' % (
                build.repo_id.root(), build.branch_id.name, build.commit)
            if os.path.exists(build_path):
                shutil.rmtree(build_path, ignore_errors=True)
        return super(Build, self).unlink(cr, uid, ids, context=context)
