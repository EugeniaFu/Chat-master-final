import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from chatapp.models import Room, Message, User
from django.core.files.storage import default_storage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.roomGroupName = f'chat_{self.room_name}'
        self.username = self.scope["user"].username  # Asumiendo que el usuario está autenticado

        await self.channel_layer.group_add(self.roomGroupName, self.channel_name)
        await self.accept()

        # Notificar que un usuario se unió al chat
        await self.channel_layer.group_send(
            self.roomGroupName,
            {
                "type": "systemMessage",
                "message": f"{self.username} se ha unido al chat.",
            }
        )

    async def disconnect(self, close_code):
        # Notificar que un usuario salió del chat
        await self.channel_layer.group_send(
            self.roomGroupName,
            {
                "type": "systemMessage",
                "message": f"{self.username} ha salido del chat.",
            }
        )

        await self.channel_layer.group_discard(self.roomGroupName, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message = text_data_json.get("message")  # Mensaje de texto
        file_data = text_data_json.get("file_data")  # Datos del archivo en base64
        file_name = text_data_json.get("file_name")  # Nombre del archivo
        username = text_data_json["username"]
        room_name = text_data_json["room_name"]

        # Validar que al menos uno de los dos (mensaje o archivo) esté presente
        if not message and not file_data:
            return  # No procesar si no hay mensaje ni archivo

        # Guardar el mensaje (o archivo) en la base de datos
        if file_data:
            file_url = await self.save_file(file_data, file_name)
            await self.save_message(None, file_url, username, room_name)
            # Enviar el mensaje de archivo
            await self.channel_layer.group_send(
                self.roomGroupName,
                {
                    "type": "sendFile",
                    "file_url": file_url,
                    "username": username,
                }
            )
        else:
            await self.save_message(message, None, username, room_name)
            # Enviar el mensaje de texto
            await self.channel_layer.group_send(
                self.roomGroupName,
                {
                    "type": "sendMessage",
                    "message": message,
                    "username": username,
                }
            )

    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({"type": "chat", "message": message, "username": username}))

    async def sendFile(self, event):
        file_url = event["file_url"]
        username = event["username"]
        await self.send(text_data=json.dumps({"type": "file", "file_url": file_url, "username": username}))

    async def systemMessage(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "system", "message": message}))

    @sync_to_async
    def save_message(self, message, file_url, username, room_name):
        user = User.objects.get(username=username)
        room = Room.objects.get(name=room_name)

        if file_url:
            Message.objects.create(user=user, room=room, attachment=file_url)
        else:
            Message.objects.create(user=user, room=room, content=message)

    @sync_to_async
    def save_file(self, file_data, file_name):
        # Decodificar el archivo en base64
        file_data = base64.b64decode(file_data.split(',')[1])
        file_path = f'chatapp/uploads/{file_name}'  # Ruta donde se almacenará el archivo
        file_content = ContentFile(file_data)
        # Guardar el archivo en el almacenamiento
        file_url = default_storage.save(file_path, file_content)  
        # Obtener la URL pública del archivo, ahora asegurándonos de que no haya duplicación en la ruta
        file_url = default_storage.url(file_url).replace('/media/media/', '/media/')  # Corregir la duplicación
        return file_url
