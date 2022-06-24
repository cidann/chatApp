from django.urls import re_path
from . import consumers
websocket_urlpatterns=[
    re_path(r'group/(?P<groupID>\d+)',consumers.groupChat.as_asgi()),
    re_path(r'join',consumers.join.as_asgi())
]