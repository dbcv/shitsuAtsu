from django import forms
from django.contrib.auth.models import User

from .models import Profile


class SimpleSignUpForm(forms.ModelForm):
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput,
        help_text="8文字以上で入力してください。",
    )

    password_confirm = forms.CharField(
        label="パスワード（確認）",
        widget=forms.PasswordInput,
    )

    email = forms.EmailField(
        label="メールアドレス",
        required=False,
    )

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error(
                "password_confirm",
                "パスワードが一致しません。",
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label="メールアドレス",
        required=False,
    )

    class Meta:
        model = Profile
        fields = ("email", "age", "gender")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["age"].label = "年齢"
        self.fields["gender"].label = "性別"
        if self.instance and hasattr(self.instance, "user") and self.instance.user:
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if "email" in self.cleaned_data:
            profile.user.email = self.cleaned_data["email"]
            if commit:
                profile.user.save()
        return profile


import re

from django.core.exceptions import ValidationError

USERNAME_REGEX = re.compile(r"^[0-9A-Za-z_]+$")


class SimplePasswordChangeForm(forms.ModelForm):
    new_password = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ()

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        if not USERNAME_REGEX.match(password):
            raise ValidationError(
                "パスワードは英数字とアンダースコアのみ使用できます。"
            )
        return password

    def save(self, commit=True):
        user = self.instance
        user.set_password(self.cleaned_data["new_password"])
        if commit:
            user.save()
        return user
