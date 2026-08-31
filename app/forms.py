from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CadastroForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="E-mail"
    )

    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="Nome"
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        label="Sobrenome"
    )
    
    def clean_email(self):

        email = self.cleaned_data["email"]

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "Este e-mail já está cadastrado."
            )

        return email

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2"
        ]


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Usuário ou E-mail",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Usuário ou e-mail",
                "autofocus": True
            }
        )
    )

    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Digite sua senha"
            }
        )
    )

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:

            try:
                usuario = User.objects.get(
                    email__iexact=username
                )

                username = usuario.username

                self.cleaned_data["username"] = username

            except User.DoesNotExist:
                pass

        return super().clean()