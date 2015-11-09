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
        'views/repo_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
