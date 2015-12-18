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


class Repository(models.Model):
    _inherit = 'runbot.repo'

    # Fields
    provider = fields.Selection(
        selection_add=[('bitbucket', 'Bitbucket')], required=True)

    @api.model
    def get_bitbucket_token(self):
        token_param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'bitbucket.password')], limit=1)
        if not token_param:
            raise Warning(_('Missing "bitbucket.password" system parameter!'))
        return token_param.value

    @api.model
    def get_bitbucket_username(self):
        username_param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'bitbucket.username')], limit=1)
        if not username_param:
            raise Warning(_('Missing "bitbucket.username" system parameter!'))
        return username_param.value

    @api.model
    def get_bitbucket_url(self):
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'bitbucket.url')], limit=1)
        if not param:
            raise Warning(_('Missing "bitbucket.url" system parameter!'))
        return param.value

    @api.multi
    def bitbucket_get_repo(self):
        self.ensure_one()
        endpoint = '/repositories/'
        # Get all repositories to which the use has explicit read access
        r = requests.get('%s%s' % (self.get_bitbucket_url(), endpoint),
                         params={'role': 'member'},
                         auth=(self.get_bitbucket_username(),
                               self.get_bitbucket_token()))
        try:
            response = r.json()
            for repo in response['values']:
                for link in repo['links']['clone']:
                    if self.name in link['href']:
                        return repo['full_name']
        except ValueError:
            raise Warning(_('Couldn\'t get repo from Bitbucket Server'))
        return False

    @api.multi
    def bitbucket_get_commit(self, sha):
        self.ensure_one()
        repo = self.bitbucket_get_repo()
        if repo:
            endpoint = '/repositories/%s/commit/%s' % (repo, sha)
            r = requests.get('%s%s' % (self.get_bitbucket_url(), endpoint),
                             auth=(self.get_bitbucket_username(),
                                   self.get_bitbucket_token()))
            try:
                response = r.json()
                return response
            except ValueError:
                raise Warning(_('Couldn\'t get commit from Bitbucket Server'))
        return False

    @api.multi
    def bitbucket_process_push_hook(self, token, request):
        self.ensure_one()
        bb_repo = self.bitbucket_get_repo()
        commit = self.bitbucket_get_commit(
            request['push']['changes'][0]['commits'][0]['hash'])
        if self and bb_repo == request['repository']['full_name'] and commit:
            branch = self.env['runbot.branch'].sudo().search([
                ('ref_name', '=', request['ref']),
                ('repo_id', '=', self.id)], limit=1)
            build = self.env['runbot.build'].sudo().search([
                ('repo_id.id', '=', self.id),
                ('branch_id.ref_name', '=', request['ref']),
                ('commit', '=', commit['hash'])], limit=1)
            if not build:
                build = self.env['runbot.build'].sudo().create({
                    'commit': commit['hash'],
                    'branch_id': branch.id,
                })
            return build
        _logger.info('Couldn\'t process webhook from Bitbucket server!')
        return False
