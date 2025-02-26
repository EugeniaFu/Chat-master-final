from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Room(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=100)

    def __str__(self):
        return f"Room: {self.name} | Id: {self.slug}"

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)  # Mensaje opcional si es solo archivo
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=now)  # Usa la hora del sistema
    attachment = models.FileField(upload_to="chat_files/", blank=True, null=True)  # Permitir archivos adjuntos

    def __str__(self):
        return f"Message from {self.user.username}: {self.content or '[Attachment]'}"