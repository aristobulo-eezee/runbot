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
from openerp import http
from openerp.http import request
from openerp.addons.website.models.website import slug
from openerp.fields import Datetime

import logging
import socket
from ago import human


_logger = logging.getLogger(__name__)


class RunbotController(http.Controller):
    @staticmethod
    def time_ago(from_):
        if from_ is None:
            from_ = Datetime.now()
        return human(Datetime.from_string(from_), 1)

    @http.route('/runbot/webhook/push', type='json', auth="none")
    def push_event(self, req):
        env = request.env
        json_dict = req.jsonrequest
        token = req.httprequest.args.get('token')
        # Read information sent from webhook
        build = env['runbot.repo'].process_push_hook(token, json_dict)
        if build:
            env['runbot.build'].sudo().schedule(build.id)
        return {}

    @http.route('/runbot/webhook/build', type='json', auth="none")
    def build_event(self, req):
        env = request.env
        json_dict = req.jsonrequest
        token = req.httprequest.args.get('token')
        # Read information sent from webhook
        build = env['runbot.repo'].process_build_hook(token, json_dict)
        if build:
            env['runbot.build'].sudo().schedule(build.id)
        return {}

    @http.route('/runbot/', type='http', auth="public", website=True)
    def home(self):
        env = request.env
        repos = env['runbot.repo'].sudo().search([
            ('published', '=', True), ])
        context = {
            'repos': repos,
            'slug': slug,
            'breadcrumbs': [
                {
                    'string': 'Repositories',
                    'url': '/runbot',
                    'active': False,
                },
            ],

        }
        return request.website.render('runbot.home', context)

    @http.route('/runbot/repo/<model("runbot.repo"):repo>',
                type='http', auth="public", website=True)
    def repo(self, repo):
        env = request.env
        branches = env['runbot.branch'].sudo().search([
            ('repo_id', '=', repo.id)]).sorted(
            key=lambda r: r not in r.repo_id.sticky_branch_ids)
        context = {
            'time_ago': self.time_ago,
            'fqdn': socket.getfqdn(),
            'repo': repo,
            'branches': branches,
            'slug': slug,
            'breadcrumbs': [
                {
                    'string': 'Repositories',
                    'url': '/runbot',
                    'active': False,
                },
                {
                    'string': repo.name,
                    'url': '/runbot/repo/%s' % slug(repo),
                    'active': True,
                },
            ],
        }
        return request.website.render('runbot.repo', context)

    @http.route('/runbot/build/<model("runbot.build"):build>/start',
                type='http', auth="public", website=True)
    def start_build(self, build):
        try:
            build.sudo().start_server()
        except Exception as e:
            _logger.error(e)
            build.sudo().run()

        return request.redirect('/runbot/repo/%s' % slug(build.repo_id))
