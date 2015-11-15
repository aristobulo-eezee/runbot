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
from openerp import models, fields, api, _

import logging
import subprocess
import os
import shutil
import socket
import virtualenv
import signal
import psutil
import datetime
import json

_logger = logging.getLogger(__name__)


class Build(models.Model):
    _name = 'runbot.build'
    _rec_name = 'commit'
    _order = 'id desc'

    # Fields
    commit = fields.Char(string='Commit', required=True)
    state = fields.Selection([
        ('scheduled', _('Scheduled')),
        ('creation', _('Creation')),
        ('installing', _('Installing')),
        ('running', _('Running')),
        ('killed', _('Killed')),
        ('stopped', _('Stopped')), ], string='Status', default='scheduled')
    last_state_since = fields.Datetime(
        string='Since', default=fields.Datetime.now())
    branch_id = fields.Many2one(
        'runbot.branch', string='Branch', required=True, ondelete='cascade')
    repo_id = fields.Many2one(
        'runbot.repo', string='Repository', related='branch_id.repo_id',
        store=True)
    pid = fields.Integer(string='Process ID')
    nginx_pid = fields.Integer(string='Nginx PID')
    port = fields.Integer(string='Port')
    lp_port = fields.Integer(string='Longpolling Port')
    env_dir = fields.Char(string='Virtualenv', compute='_compute_dirs')
    parts_dir = fields.Char(string='Parts', compute='_compute_dirs')
    custom_dir = fields.Char(string='Custom modules', compute='_compute_dirs')
    odoo_dir = fields.Char(string='Odoo', compute='_compute_dirs')
    short_name = fields.Char(string='Short name', compute='_compute_dirs')

    @api.depends('commit', 'branch_id', 'branch_id.name', 'repo_id')
    def _compute_dirs(self):
        for build in self:
            build.short_name = '%s-%s' % \
                               (build.commit[:8],
                                build.branch_id.name.replace('/', '-'))
            build.env_dir = '%sbuild/%s' % (
                build.repo_id.root(), build.short_name)
            build.parts_dir = '%s/parts' % build.env_dir
            build.custom_dir = '%s/custom' % build.parts_dir
            build.odoo_dir = '%s/odoo' % build.parts_dir

    @api.multi
    def kill(self):
        """
        Send SIGKILL to build's process
        :return:
        """
        for build in self:
            _logger.info('Killing build: %s' % build.short_name)
            if build.pid and psutil.pid_exists(build.pid):
                try:
                    os.kill(build.pid, signal.SIGKILL)
                except Exception as e:
                    _logger.error(e)
            build.write({
                'port': None,
                'lp_port': None,
                'pid': None,
                'state': 'killed'})
        return True

    @api.multi
    def install_server(self):
        self.ensure_one()
        self.state = 'installing'
        runbot_cfg = self.read_json()

        if self.pid and psutil.pid_exists(self.pid):
            return False
        venv = os.environ.copy()
        _logger.info('Install odoo on build: %s' % self.short_name)
        _logger.info('Get open ports for odoo and longpolling.')
        odoo_port = self.get_open_port()
        lp_port = self.get_open_port()
        _logger.info('Found %s and %s.' % (odoo_port, lp_port))

        _logger.info('Installing odoo server.')

        # Prepare command
        addons_path = '--addons-path='
        if runbot_cfg.get('enterprise', False):
            addons_path = '%s%s/enterprise,' % (addons_path, self.parts_dir)
        cmd = [
            '%s/bin/python' % self.env_dir,
            '%s/openerp-server' % self.odoo_dir,
            '--db-filter', '%s.*$' % self.short_name,
            '%s%s/addons,%s' % (
                addons_path,
                self.odoo_dir,
                ','.join(['%s/%s' % (self.custom_dir, p)
                          for p in runbot_cfg['addons']['path']])),
            '--xmlrpc-port=%s' % odoo_port, '--longpolling-port=%s' % lp_port,
            '--logfile', '%s/logs/install.log' % self.env_dir,
            '-d', self.short_name,
            '-i', '%s' % ','.join(runbot_cfg['addons']['install']),
            '--stop-after-init']

        if runbot_cfg.get('without-demo', False):
            cmd_without_demo = list(cmd)
            cmd_without_demo.append(
                '--without-demo=%s' % runbot_cfg['without-demo'])
            odoo_server = subprocess.Popen(cmd_without_demo, env=venv)
            odoo_server.wait()

        # Now install demo data
        odoo_server = subprocess.Popen(cmd, env=venv)
        odoo_server.wait()

        return True

    @api.multi
    def start_server(self):
        """
        Run odoo build
        :return: boolean
        """
        self.ensure_one()
        runbot_cfg = self.read_json()

        if self.pid and psutil.pid_exists(self.pid):
            return False
        venv = os.environ.copy()
        _logger.info('Starting build: %s' % self.short_name)
        _logger.info('Get open ports for odoo and longpolling.')
        odoo_port = self.get_open_port()
        lp_port = self.get_open_port()
        _logger.info('Found %s and %s.' % (odoo_port, lp_port))
        _logger.info('Starting odoo server.')

        # Prepare command
        addons_path = '--addons-path='
        if runbot_cfg.get('enterprise', False):
            addons_path = '%s%s/enterprise,' % (addons_path, self.parts_dir)
        cmd = [
            '%s/bin/python' % self.env_dir,
            '%s/openerp-server' % self.odoo_dir,
            '--db-filter', '%s.*$' % self.short_name,
            '%s%s/addons,%s' % (
                addons_path,
                self.odoo_dir,
                ','.join(['%s/%s' % (self.custom_dir, p)
                          for p in runbot_cfg['addons']['path']])),
            '--xmlrpc-port=%s' % odoo_port, '--longpolling-port=%s' % lp_port,
            '--logfile', '%s/logs/server.log' % self.env_dir,
            '-d', self.short_name, ]

        if runbot_cfg.get('tests', False):
            cmd.append('--test-enabled')

        odoo_server = subprocess.Popen(cmd, env=venv)
        # Check if process is running
        state = psutil.pid_exists(odoo_server.pid) and 'running' or 'stopped'
        self.write({
            'pid': odoo_server.pid,
            'port': odoo_port,
            'lp_port': lp_port,
            'state': state,
        })
        return True

    @api.multi
    def clean(self):
        """
        Clean filsystem an drop database
        :return:
        """
        for build in self:
            _logger.info('Cleaning filesystem.')
            if os.path.exists(build.env_dir):
                shutil.rmtree(build.env_dir, ignore_errors=True)
            _logger.info('Dropping database %s.' % self.short_name)
            dropdb = subprocess.Popen([
                'dropdb',
                '-U', 'odoo',
                '--if-exists',
                self.short_name])
            dropdb.wait()

    @api.multi
    def prepare(self):
        """
        Prepare build instance, by default it will create a virtualenv,
        install from requirements.txt and generate a clean database
        :return:
        """
        self.ensure_one()
        self.clean()
        self.state = 'creation'

        _logger.info('Preparing build: %s' % self.short_name)
        if not os.path.exists(self.env_dir):
            virtualenv.create_environment(self.env_dir)
        if not os.path.exists(self.parts_dir):
            os.makedirs(self.parts_dir)
        if not os.path.exists(self.env_dir+'/logs'):
            os.makedirs(self.env_dir+'/logs')

        _logger.info('Cloning %s' % self.branch_id.name)
        self.repo_id.clone(branch=self.branch_id.name, to_path=self.custom_dir,
                           commit=self.commit)

        runbot_cfg = self.read_json()

        _logger.info('Cloning odoo')
        odoo_repo = self.env['runbot.repo'].search([
            ('odoo_repo', '=', True)], limit=1)
        odoo_repo.clone(branch=runbot_cfg['odoo'], to_path=self.odoo_dir)

        if runbot_cfg.get('enterprise', False):
            _logger.info('Cloning enterprise')
            enterprise_repo = self.env['runbot.repo'].search([
                ('name', '=', runbot_cfg['enterprise']['repo'])], limit=1)
            enterprise_repo.clone(branch=runbot_cfg['enterprise']['branch'],
                                  to_path=self.parts_dir+'/enterprise')

        _logger.info('Installing odoo dependencies')
        venv = os.environ.copy()
        # Fix from https://github.com/gevent/gevent/issues/656
        venv['CFLAGS'] = '-std=c99'
        pip_odoo = subprocess.Popen([
            '%s/bin/pip' % self.env_dir, 'install', '-r',
            '%s/requirements.txt' % self.odoo_dir], env=venv)
        pip_odoo.wait()

        if os.path.isfile('%s/requirements.txt' % self.custom_dir):
            _logger.info('Installing custom dependencies')
            pip_custom = subprocess.Popen([
                '%s/bin/pip' % self.env_dir, 'install', '-r',
                '%s/requirements.txt' % self.custom_dir], env=venv)
            pip_custom.wait()

        _logger.info('Creating database %s' % self.short_name)
        createdb = subprocess.Popen([
            'createdb', '--encoding=unicode', '--lc-collate=C',
            '-U', 'odoo',
            '--template=template0', self.short_name], env=venv)
        createdb.wait()

        _logger.info('Configuring nginx')
        # I like this solution so I copied it from odoo ;)
        ngx_build = {
            'short_name': self.short_name,
            'port': self.port,
            'lp_port': self.lp_port,
        }
        nginx_config = self.pool['ir.ui.view'].render(
            self.cr, self.env.user.id, 
            'runbot.nginx_template', values=ngx_build)
        open(os.path.join('../nginx/', '%s.conf' % self.short_name),
             'w').write(nginx_config)
        nginx = subprocess.Popen(['/etc/init.d/nginx', 'reload'])
        nginx.wait()

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

    @api.model
    def run(self, build_id):
        build = self.browse(build_id)
        build.kill()
        build.prepare()
        build.install_server()
        build.start_server()

    @api.model
    def schedule(self, build_id):
        """
        Adds a ir.cron to schedule a build.
        :param build_id: id of build to schedule
        """
        at = datetime.datetime.now() + datetime.timedelta(minutes=1)
        at = at.strftime('%Y-%m-%d %H:%M:%S')
        build = self.browse(build_id)
        cron = self.env['ir.cron'].sudo().create({
            'active': True,
            'name': '%s at %s' % (build.short_name, at),
            'priority': 5,
            'numbercall': 1,
            'nextcall': at,
            'model': 'runbot.build',
            'function': 'run',
            'args': '(%s, )' % build_id,
            'user_id': self.env.user.id,
        })
        _logger.info('Scheduled: %s' % cron.name)

    def unlink(self, cr, uid, ids, context=None):
        builds = self.browse(cr, uid, ids, context=context)
        for build in builds:
            build.kill()
            build.clean()
        return super(Build, self).unlink(cr, uid, ids, context=context)

    @api.model
    def create(self, values):
        res = super(Build, self).create(values)
        self.schedule(res.id)
        return res

    @api.multi
    def read_json(self):
        self.ensure_one()
        with open(self.custom_dir+'/runbot.json') as data_file:
            config = json.load(data_file)
        return config
