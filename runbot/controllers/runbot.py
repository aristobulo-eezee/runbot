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

        return request.redirect('/runbot/build/%s' % slug(build.repo_id))

    @http.route('/runbot/build/<model("runbot.build"):build>/rebuild',
                type='http', auth="public", website=True)
    def rebuild_build(self, build):
        """
        Set current build to be rebuilt, as we use cron jobs to handle build
        queues the build is sent to the scheduler
        :param build:
        :return:
        """
        env = request.env
        try:
            env['runbot.build'].schedule(build.id)
        except Exception as e:
            _logger.error(e)
        return request.redirect('/runbot/build/%s' % slug(build.repo_id))

    @http.route('/runbot/build/<model("runbot.build"):build>/kill',
                type='http', auth="public", website=True)
    def kill_build(self, build):
        try:
            build.sudo().kill()
        except Exception as e:
            _logger.error(e)
        return request.redirect('/runbot/build/%s' % slug(build.repo_id))

    @http.route('/runbot/build/<model("runbot.build"):build>',
                type='http', auth="public", website=True)
    def build_details(self, build):
        tec_info = self.get_technical_information(build)
        state = build.state
        context = {
            'time_ago': self.time_ago,
            'build': build,
            'fqdn': socket.getfqdn(),
            'slug': slug,
            'tec_info': tec_info,
            'state': state,
            'breadcrumbs': [
                {
                    'string': 'Repositories',
                    'url': '/runbot',
                    'active': False,
                },
                {
                    'string': build.repo_id.name,
                    'url': '/runbot/repo/%s' % slug(build.repo_id),
                    'active': False,
                },
                {
                    'string': 'Build: %s' % build.short_name,
                    'url': '/runbot/build/%s' % slug(build),
                    'active': True,
                },
            ],
        }
        return request.website.render('runbot.build_details', context)

    def get_technical_information(self, build):
        """
        Get technicals information about the Build.
        Define field to display into a list and search his label.
        Then, get the value of each field.
        If a field is a M2O, take the 'display_name' field to display it
        Args:
            build: runbot.build recordset

        Returns: dict

        """
        field_obj = request.env['ir.model.fields']
        model_obj = request.env['ir.model']
        model = model_obj.search([('model', '=', 'runbot.build')], limit=1)
        # Fields to display
        field_names = ['branch_id', 'repo_id', 'lp_port', 'pid', 'port',
                       'commit']
        information = {}
        criterion = [('name', 'in', field_names), ('model_id', '=', model.id)]
        fields_found = field_obj.search(criterion, limit=len(field_names))
        for field in fields_found:
            # Be careful, the label of the field is the key of the dict!
            field_value = getattr(build, field.name, '')
            if field.ttype == 'many2one':
                field_value = field_value.display_name
            information.update({
                field.field_description: field_value,
            })
        return information
