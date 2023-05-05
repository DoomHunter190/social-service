from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordChangeDoneView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class MyPasswordResetDoneView(PasswordResetDoneView):

    template_name = 'users/password_reset_done.html'


class MyPasswordResetView(PasswordResetView):

    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_form.html'


class MyPasswordChangeView(PasswordChangeView):

    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'


class MyPasswordChangeDoneView(PasswordChangeDoneView):

    template_name = 'users/password_change_done.html'


class MyPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'


class MyPasswordResetCompleteView(PasswordResetCompleteView):

    template_name = 'users/password_reset_complete.html'
