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
{
    'name': 'Runbot',
    'version': '0.1',
    'author': 'Eezee-It',
    'category': 'Generic Module',
    'website': 'http://www.eezee-it.com',
    'summary': 'Runbot',
    'description': """
Runbot
======


Eezee-It's replacement for official Odoo's runbot.
It helps you to automatically run Odoo instances. It doesn't run pytests,
only helps you to hook a repo and trigger builds.

Builds will generate a new instance of the related branch and install it
with or without demo data.

Tests will run on a CI software of you choice (Travis-ci, Gitlab-ci,
Drone, etc.)
""",
    'depends': ['website'],
    'data': [
        'views/runbot_view.xml',
        'views/runbot_template.xml',
        'views/build_details.xml',
        'views/nginx_template.xml',
        'views/odoo_conf_template.xml',
        'views/repo_view.xml',
        'views/build_view.xml',
        'data/runbot_data.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
