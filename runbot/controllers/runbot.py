# -*- encoding: utf-8 -*-
from openerp import http
from openerp.http import request


class RunbotController(http.Controller):
    @http.route('/runbot/webhook/receive_signal',
                type='json', auth="none")
    def receive_signal(self, req):
        env = request.env
        json_dict = req.jsonrequest
        # Read information sent from webhook
        ref = json_dict['ref']
        repo = json_dict['repository']['url']
        commit = json_dict['commits'][0]
        build = env['runbot.build'].sudo().search([
            ('repo_id.name', '=', repo),
            ('branch_id.ref_name', '=', ref),
            ('commit', '=', commit['id'])], limit=1)
        if not build:
            repo = env['runbot.repo'].sudo().search([
                ('name', '=', repo)], limit=1)
            branch = env['runbot.branch'].sudo().search([
                ('ref_name', '=', ref),
                ('repo_id', '=', repo and repo.id)], limit=1)
            build = env['runbot.build'].sudo().create({
                'commit': commit['id'],
                'branch_id': branch.id,
            })
        build.sudo().prepare()
        return {}
