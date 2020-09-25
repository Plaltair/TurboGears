# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, lurl
from tg import request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.exceptions import HTTPFound
from tg import predicates
from contatti import model
from contatti.controllers.secure import SecureController
from contatti.model import DBSession
from contatti.model.auth import User
from contatti.model.contact import PhoneBook
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController

from contatti.lib.base import BaseController
from contatti.controllers.error import ErrorController

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the contatti application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()
    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()

    @expose("contatti.templates.registration")
    def registration(self, username=None, email=None, password=None):
        if username is None and email is None and password is None:
            return dict(page="registration")
        else:
            DBSession.add(User(user_name=username, email_address=email, password=password))
            redirect("/login")

    @expose("contatti.templates.contacts")
    def contacts(self):
        if request.identity:
            current_user = User.by_email_address(request.identity['repoze.who.userid'])
            contacts = DBSession.query(PhoneBook).filter(PhoneBook.id_user == current_user.user_id).order_by(PhoneBook.name).all()
            return dict(page="contacts", contacts=contacts)
        else:
            redirect("/login")

    @expose("json")
    def contacts_json(self):
        if request.identity:
            current_user = User.by_email_address(request.identity['repoze.who.userid'])
            contacts = DBSession.query(PhoneBook).filter(PhoneBook.id_user == current_user.user_id).order_by(PhoneBook.name).all()
            return dict(page="contacts", contacts=contacts)
        else:
            redirect("/login")

    @expose("contatti.templates.add_contact")
    def add_contact(self, id=None, name=None, number=None):
        if request.identity:
            if name is None and number is None:
                return dict(page="add_contact")
            else:
                if id is None:
                    current_user = User.by_email_address(request.identity['repoze.who.userid'])
                    DBSession.add(PhoneBook(id_user=current_user.user_id, name=name, number=number))
                else:
                    row = DBSession.query(PhoneBook).filter(PhoneBook.id == id).first()
                    row.name = name
                    row.number = number

                redirect("contacts/")
        else:
            redirect("/login")

    @expose("contatti.templates.modify_contact")
    def modify_contact(self, id=None, name=None, number=None):
        if request.identity:
            if id is not None and name is not None and number is not None:
                return dict(page="modify_contact", id=id, name=name, number=number)
        else:
            redirect("/login")

    @expose()
    def delete_contact(self, id=None):
        if request.identity:
            DBSession.query(PhoneBook).filter(PhoneBook.id == id).delete()
            redirect("/contacts")
        else:
            redirect("/login")

    def _before(self, *args, **kw):
        tmpl_context.project_name = "contatti"

    @expose('contatti.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')
    @expose('contatti.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('contatti.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(page='environ', environment=request.environ)

    @expose('contatti.templates.data')
    @expose('json')
    def data(self, **kw):
        """
        This method showcases how you can use the same controller
        for a data page and a display page.
        """
        return dict(page='data', params=kw)
    @expose('contatti.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('contatti.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('contatti.templates.login2')
    def login(self, came_from=lurl('/'), failure=None, login=''):
        """Start the user login."""
        if failure is not None:
            if failure == 'user-not-found':
                flash(_('User not found'), 'error')
            elif failure == 'invalid-password':
                flash(_('Invalid Password'), 'error')

        login_counter = request.environ.get('repoze.who.logins', 0)
        if failure is None and login_counter > 0:
            flash(_('Wrong credentials'), 'warning')

        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from, login=login)

    @expose()
    def post_login(self, came_from=lurl('/contacts')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)

        # Do not use tg.redirect with tg.url as it will add the mountpoint
        # of the application twice.
        return HTTPFound(location=came_from)

    @expose()
    def post_logout(self):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        return HTTPFound(location="/login")
