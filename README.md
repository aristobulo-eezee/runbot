RUNBOT
======

Eezee-It's replacement for official Odoo's runbot.

It helps you to automatically run Odoo instances. It doesn't run pytests,
only helps you to hook a repo and trigger builds.

Builds will generate a new instance of the related branch and install it
with or without demo data.

Tests will run on a CI software of you choice (Travis-ci, Gitlab-ci, Drone, etc.)
