[![build status](https://gitlab.com/ci/projects/19298/status.png?ref=master)](https://gitlab.com/ci/projects/19298?ref=master)

RUNBOT
======

Eezee-It's replacement for official Odoo's runbot.

It helps you to automatically run Odoo instances. It doesn't run pytests,
only helps you to hook a repo and trigger builds.

Builds will generate a new instance of the related branch and install it
with or without demo data.

Tests will run on a CI software of you choice (Travis-ci, Gitlab-ci, Drone, etc.)

### Config

To configure how runbot will build an instance of your repository you need 
to add a runbot.json file to your repository root directory.

Example:

```
{
  "odoo": "9.0",
  "without-demo": "all",
  "addons": {
    "path": ["addons"],
    "install": ["runbot"]
  },
  "enterprise": {
    "branch": "9.0",
    "repo": "git@host:odoo/enterprise.git"
  }
}
```

You can set which odoo version to use, set modules to install and modify the
addons path.


### Submodules

By default, it does support submodules. No configuration needed, just be sure
you have ssh access to all your repositories.


### Providers

You can set any git provider (Github, Bitbucket, Gitlab, local repositories, 
etc.).

For private repositories you need to use your repo's ssh url.


### What's different on this runbot?

**This is not a fork of Odoo's runbot**, this was written from scratch. It works
on Odoo v9 (it should also run on v8) and uses default Python libraries to
make all git operations. 

It uses virtualenv, which means that every build gets its own virtualenv
and dependencies are installed from requirements.txt (if file is present).

Also, it's clean, all code is PEP-8 compliant and organised following Odoo's 
guidelines. 

It will drop all created databases and clean the filesystem as you delete
repositories and builds.

Control, from Odoo's backend you can control each build. It has 'Rebuild',
'Kill' and 'Start' actions.