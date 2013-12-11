from django.contrib.auth.models import User, Group
from django import forms
from smartmin.users.views import UserCRUDL as SmartminUserCRUDL
from smartmin.users.views import UserUpdateForm
from rapidsms.models import Backend
from smartmin.views import *
from .models import UserBackend
import re

class BackendUserForm(UserUpdateForm):
    backends = forms.ModelMultipleChoiceField(queryset=Backend.objects.all(), widget=forms.CheckboxSelectMultiple,
                                              help_text="Which backends this user can create polls for")

    class Meta:
        model = User
        fields = ('username', 'new_password', 'first_name', 'last_name', 'email', 'groups', 'backends', 'is_active', 'last_login')

class BackendUserCRUDL(SmartminUserCRUDL):

    def permission_for_action(self, action):
        """
        Returns the permission to use for the passed in action
        """
        return "%s.%s_%s" % ('auth', self.model_name.lower(), action)

    def template_for_action(self, action):
        """
        Returns the template to use for the passed in action
        """
        return "%s/%s_%s.html" % ('users', self.model_name.lower(), action)

    def url_name_for_action(self, action):
        """
        Returns the reverse name for this action
        """
        return "%s.%s_%s" % ('users', self.model_name.lower(), action)

    class Update(SmartminUserCRUDL.Update):
        form_class = BackendUserForm
        fields = ('username', 'new_password', 'first_name', 'last_name', 'email', 'groups', 'backends', 'is_active', 'last_login')

        def get_form_class(self):
            form_class = super(BackendUserCRUDL.Update, self).get_form_class()
            return form_class

        def derive_initial(self):
            initial = super(BackendUserCRUDL.Update, self).derive_initial()
            initial['backends'] = [_.backend for _ in UserBackend.objects.filter(user=self.object)]
            return initial

        def post_save(self, obj):
            obj = super(BackendUserCRUDL.Update, self).post_save(obj)

            # clear out any previous backends
            UserBackend.objects.filter(user=self.object).delete()
            for backend in self.form.cleaned_data['backends']:
                UserBackend.objects.create(user=self.object, backend=backend)

            return obj

