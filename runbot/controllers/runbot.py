# -*- encoding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp.addons.website.models.website import slug

import logging

_logger = logging.getLogger(__name__)


class RunbotController(http.Controller):
    @http.route('/runbot/webhook/push',
                type='json', auth="none")
    def push_event(self, req):
        env = request.env
        json_dict = req.jsonrequest
        token = req.httprequest.args.get('token')
        # Read information sent from webhook
        ref = json_dict['ref']
        repo = json_dict['repository']['url']
        commit = json_dict['commits'][0]
        # Verify token before continue
        repository = env['runbot.repo'].sudo().search([
            ('name', '=', repo), ('token', '=', token)], limit=1)
        if not repository:
            _logger.info('Received wrong token for repo: %s' % repo)
            return
        build = env['runbot.build'].sudo().search([
            ('repo_id.id', '=', repository.id),
            ('branch_id.ref_name', '=', ref),
            ('commit', '=', commit['id'])], limit=1)
        if not build:
            branch = env['runbot.branch'].sudo().search([
                ('ref_name', '=', ref),
                ('repo_id', '=', repository and repository.id)], limit=1)
            env['runbot.build'].sudo().create({
                'commit': commit['id'],
                'branch_id': branch.id,
            })
        else:
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
        context = {
            'repo': repo,
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
