# -*- encoding: utf-8 -*-
import openerp
from openerp import models, fields, api, _
from openerp.exceptions import Warning, ValidationError

import os
import uuid
import shutil
from git import Repo, RemoteReference, TagReference, Head


class Repository(models.Model):
    _name = 'runbot.repo'

    # Fields
    active = fields.Boolean('Active', default=True)
    odoo_repo = fields.Boolean('Default Odoo repository', default=False)
    alias = fields.Char('Alias')
    name = fields.Char('Repository', required=True)
    published = fields.Boolean('Available on website', default=False,
                               copy=False)
    git_host = fields.Selection([
        ('local', _('Local')),
        ('github', _('Github')), ], string='Hosting', required=True,
        default='github',
        help='Provider where git repository is hosted. Local means git '
             'repository is located on the same filesystem as runbot.')
    branch_ids = fields.One2many('runbot.branch', 'repo_id', string='Branches')
    sticky_branch_ids = fields.Many2many(
        'runbot.branch', string='Sticky branches', copy=False)
    tag_ids = fields.One2many('runbot.repo.tag', 'repo_id', string='Tags')
    token = fields.Char(
        string='Auth Token', default=lambda self: uuid.uuid4().hex,
        help='Use this token in your webhooks to authenticate.'
             'Example: http://example.com/runbot/webhook/push?'
             'token=8c05904f0051419283d1024fc5ce1a59')

    _sql_constraints = [
        ('unq_name', 'unique(name)', 'Repository must be unique!'),
    ]

    @api.multi
    @api.constrains('odoo_repo')
    def _check_description(self):
        self.ensure_one()
        count = self.env['runbot.repo'].search_count([
            ('odoo_repo', '=', True)])
        if count > 1:
            raise ValidationError("Can\'t have more than one default odoo "
                                  "repository")

    @api.model
    def root(self):
        return os.path.join(os.path.dirname(openerp.addons.runbot.__file__),
                            'static/')

    @api.multi
    def get_plain_name(self):
        self.ensure_one()
        name = self.name
        for i in './@:':
            name = name.replace(i, '_')
        return name

    @api.multi
    def get_dir(self):
        self.ensure_one()
        return '%srepo/%s' % (self.root(), self.get_plain_name())

    @api.model
    def create(self, values):
        res = super(Repository, self).create(values)
        res.clone()
        return res

    def unlink(self, cr, uid, ids, context=None):
        repos = self.browse(cr, uid, ids, context=context)
        for repo in repos:
            if os.path.exists(repo.get_dir()):
                shutil.rmtree(repo.get_dir(), ignore_errors=True)
        return super(Repository, self).unlink(cr, uid, ids, context=context)

    @api.multi
    def clone(self, branch=None, to_path=None):
        """
        Shallow clone a repository, if branch name is specified it will clone
        only that branch
        :param branch: string: branch name
        :param to_path: string: destination dir
        :return:
        """
        self.ensure_one()
        try:
            if not branch:
                # Create bare repo
                repo = Repo.clone_from(
                    self.name, self.get_dir(), depth=1, no_single_branch=True,
                    bare=True)
            else:
                # Get sources from bare repo
                repo = Repo.clone_from(
                    self.get_dir(), to_path=to_path, depth=1, branch=branch)
            heads = []
            tags = []
            for ref in repo.references:
                if isinstance(ref, (RemoteReference, Head)):
                    heads.append((ref.name, ref.path))
                elif isinstance(ref, TagReference):
                    tags.append(ref.name)
            self.update_branches(heads=heads)
            self.update_tags(tags=tags)
        except Exception as e:
            raise Warning(e)

    @api.multi
    def update_branches(self, heads=[]):
        """
        Update repository branches from a list of heads. Creates heads not
        present in branch_ids and clean deleted branches.
        :param heads: list of branches
        :return:
        """
        self.ensure_one()
        branches = [b.ref_name for b in self.branch_ids]
        for head in heads:
            if 'origin/HEAD' not in head[1] and head[0] not in branches:
                values = {
                    'repo_id': self.id,
                    'name': head[0],
                    'ref_name': head[1].replace('refs/remotes/origin/',
                                                'refs/heads/'),
                }
                self.env['runbot.branch'].create(values)

    @api.multi
    def update_tags(self, tags=[]):
        """
        Update repository tags. Create tags not
        present in tag_ids and clean deleted tags.
        :param tags: list of tags
        :return:
        """
        self.ensure_one()
        repo_tags = [t.name for t in self.tag_ids]
        for tag in tags:
            if tag not in repo_tags:
                self.env['runbot.repo.tag'].create({
                    'repo_id': self.id,
                    'name': tag})

    @api.multi
    def repo_publish_button(self):
        for repo in self:
            repo.published = not repo.published
