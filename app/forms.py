from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import PerfilUsuario


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(label="Usuário", max_length=150, required=True)
    first_name = forms.CharField(label="Nome", max_length=150, required=False)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    telefone = forms.CharField(label="Telefone", max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'perfil'):
            self.fields['telefone'].initial = self.instance.perfil.telefone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def save(self, commit=True):
        user = super().save(commit=commit)
        telefone = self.cleaned_data.get('telefone')
        
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.telefone = telefone
        if commit:
            perfil.save()
        return user


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
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

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
            
        try:
            return super().clean()
        except forms.ValidationError:
            raise forms.ValidationError(
                "Usuário/e-mail ou senha incorretos."
            )