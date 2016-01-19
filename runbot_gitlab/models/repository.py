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
from openerp.exceptions import Warning

import requests
import logging

_logger = logging.getLogger(__name__)

GITLAB_API = '/api/v3'
GITLAB_CI_API = '/api/v1'


class Repository(models.Model):
    _inherit = 'runbot.repo'

    # Fields
    provider = fields.Selection(
        selection_add=[('gitlab', 'Gitlab')], required=True)
    ci_service = fields.Selection(selection_add=[('gitlab_ci', 'Gitlab CI')])

    @api.model
    def get_gitlab_token(self):
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'gitlab.token')], limit=1)
        if not param:
            raise Warning(_('Missing "gitlab.token" system parameter!'))
        return param.value

    @api.model
    def get_gitlab_url(self):
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'gitlab.url')], limit=1)
        if not param:
            raise Warning(_('Missing "gitlab.url" system parameter!'))
        return param.value

    @api.multi
    def gitlab_get_project_id(self):
        self.ensure_one()
        payload = {'private_token': self.get_gitlab_token()}
        endpoint = '/projects/'
        r = requests.get('%s%s%s' % (self.get_gitlab_url(), GITLAB_API,
                                     endpoint), params=payload)
        try:
            response = r.json()
            for prj in response:
                if self.name in [prj['ssh_url_to_repo'],
                                 prj['http_url_to_repo']]:
                    return prj['id']
        except ValueError:
            raise Warning(_('Couldn\'t get project from Gitlab Server'))
        return False

    @api.multi
    def gitlab_get_commit(self, sha):
        self.ensure_one()
        prj_id = self.gitlab_get_project_id()
        if prj_id:
            payload = {'private_token': self.get_gitlab_token()}
            endpoint = '/projects/%s/repository/commits/%s' % (prj_id, sha)
            r = requests.get('%s%s%s' % (self.get_gitlab_url(), GITLAB_API,
                                         endpoint), params=payload)
            try:
                response = r.json()
                return response
            except ValueError:
                raise Warning(_('Couldn\'t get commit from Gitlab Server'))
        return False

    @api.multi
    def gitlab_process_push_hook(self, token, request):
        self.ensure_one()
        _logger.info('Processing Gitlab push hook...')
        prj_id = self.gitlab_get_project_id()
        commit = self.gitlab_get_commit(request['commits'][0]['id'])
        if self and prj_id == request.get('project_id', None) and commit:
            _logger.info('Token accepted, preparing build.')
            # TODO: This way to update repo has to be improved
            self.clone(branch=request['ref'][len('refs/heads/'):])
            branch = self.env['runbot.branch'].sudo().search([
                ('ref_name', '=', request['ref']),
                ('repo_id', '=', self.id)], limit=1)
            build = self.env['runbot.build'].sudo().search([
                ('repo_id.id', '=', self.id),
                ('branch_id.ref_name', '=', request['ref']),
                ('commit', '=', commit['id'])], limit=1)
            if not build:
                build = self.env['runbot.build'].sudo().create({
                    'commit': commit['id'],
                    'branch_id': branch.id,
                })
            return build
        _logger.info('Couldn\'t process webhook from Gitlab server!')
        return False

    @api.multi
    def gitlab_ci_process_build_hook(self, token, request):
        self.ensure_one()
        _logger.info('Processing Gitlab CI build hook...')
        if self.env['runbot.build'].search([
                ('commit', '=', request['sha']),
                ('branch_id.name', '=', request['ref'])]):
            # For a reason I haven't discover yet, sometimes same build hook
            # is received multiple times, so let's check
            # before if we already have an existing build
            _logger.info('Skipping commit %s in %s',
                         (request['sha'][:7], request['ref']))
            return False
        prj_id = self.gitlab_get_project_id()
        commit = self.gitlab_get_commit(request['sha'])
        status = commit and commit['status']
        _logger.info('Gitlab CI build status: %s', status)
        if prj_id == request.get('project_id', None) and status == 'success':
            _logger.info('Token accepted, preparing build.')
            # TODO: This way to update repo has to be improved
            self.clone(branch=request['ref'])
            branch = self.env['runbot.branch'].sudo().search([
                ('name', '=', request['ref']),
                ('repo_id', '=', self.id)], limit=1)
            build = self.env['runbot.build'].sudo().search([
                ('repo_id.id', '=', self.id),
                ('branch_id.ref_name', '=', request['ref']),
                ('commit', '=', commit['id'])], limit=1)
            if not build:
                build = self.env['runbot.build'].sudo().create({
                    'commit': commit['id'],
                    'branch_id': branch.id,
                })
            return build
        return False

    @api.model
    def get_gitlab_ci_token(self):
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'gitlab.ci.token')], limit=1)
        if not param:
            raise Warning(_('Missing "gitlab.ci.token" system parameter!'))
        return param.value

    @api.model
    def get_gitlab_ci_url(self):
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'gitlab.ci.url')], limit=1)
        if not param:
            raise Warning(_('Missing "gitlab.ci.url" system parameter!'))
        return param.value

    @api.multi
    def gitlab_ci_get_gitlab_project_id(self, prj_id):
        self.ensure_one()
        payload = {'private_token': self.get_gitlab_ci_token()}
        endpoint = '/projects/%id' % prj_id
        r = requests.get('%s%s%s' % (self.get_gitlab_ci_url(), GITLAB_CI_API,
                                     endpoint), params=payload)
        try:
            response = r.json()
            return response['gitlab_id']
        except ValueError:
            raise Warning(_('Couldn\'t get project from Gitlab CI Server'))
        return False
