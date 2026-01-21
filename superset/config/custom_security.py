"""
Custom Security Manager for FormaSup BI - French Login Page

This module provides a custom security manager that overrides the default
Superset login view to use a French-language login template.
"""

from flask import render_template, request, redirect, flash
from flask_appbuilder.security.views import AuthDBView
from flask_appbuilder import expose
from flask_login import login_user
from superset.security import SupersetSecurityManager


class FrenchAuthDBView(AuthDBView):
    """Custom login view with French template."""

    login_template = 'appbuilder/general/security/login_db.html'

    @expose('/login/', methods=['GET', 'POST'])
    def login(self):
        """Custom login method using French template."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = self.appbuilder.sm.find_user(username=username)
            if user and self.appbuilder.sm.check_password(user, password):
                login_user(user)
                return redirect(self.appbuilder.get_url_for_index)
            else:
                flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')

        return self.render_template(
            self.login_template,
            title='Connexion',
            appbuilder=self.appbuilder
        )


class FormaSupersetSecurityManager(SupersetSecurityManager):
    """Custom security manager with French login page."""

    authdbview = FrenchAuthDBView
