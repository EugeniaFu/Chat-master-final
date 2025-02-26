from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment']  # Campos para el contenido y el archivo adjunto

    # Opcionalmente, puedes agregar validaciones para los archivos
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Validar el tipo de archivo si es necesario (por ejemplo, imágenes, PDFs)
            if not attachment.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                raise forms.ValidationError("Solo se permiten archivos PNG, JPG, JPEG, GIF o PDF.")
        return attachment


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']