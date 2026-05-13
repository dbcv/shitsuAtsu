from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Profile

class SimpleSignUpForm(forms.ModelForm):
    password = forms.CharField(
        label='パスワード', 
        widget=forms.PasswordInput,
        help_text="None"
    )

    class Meta:
        model = User
        fields = ('username',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['age', 'gender']


import re
from django.core.exceptions import ValidationError

USERNAME_REGEX = re.compile(r'^[0-9A-Za-z_]+$')

class SimplePasswordChangeForm(forms.ModelForm):
    new_password = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ()

    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        if not USERNAME_REGEX.match(password):
            raise ValidationError("パスワードは英数字とアンダースコアのみ使用できます。")
        return password

    def save(self, user, commit=True):
        user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
        return user
