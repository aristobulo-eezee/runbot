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
from openerp import models, api


class Runbot(models.Model):
    _auto = False
    _name = 'runbot.runbot'

    # Methods
    @api.model
    def clean_cron_jobs(self):
        jobs = self.env['ir.cron'].search([
            ('model', '=', 'runbot.build'),
            ('function', '=', 'run'),
            ('active', '=', False)])
        jobs.unlink()

    @api.model
    def kill_ancient_builds(self):
        max_running_builds = self.env.ref('runbot.max_running_builds').value
        max_running_builds = int(max_running_builds)
        for branch in self.env['runbot.branch'].search([]):
            running_builds = branch.build_ids.filtered(
                lambda r: r.state == 'running')
            for build in running_builds.sorted(
                    key=lambda r: r.id, reverse=True)[max_running_builds:]:
                build.kill()
                build.clean()
