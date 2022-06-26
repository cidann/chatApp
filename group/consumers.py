from channels.generic.websocket import WebsocketConsumer
from channels.auth import logout,login,get_user
from asgiref.sync import async_to_sync
from .models import *
from datetime import datetime
import json

class groupChat(WebsocketConsumer):
    def connect(self):
        self.groupID=self.scope['url_route']['kwargs']['groupID']
        self.user=self.scope['user']
        self.group=Group.objects.get(id=self.groupID)
        if(self.user in self.group.members.all() or self.group.private=='off'):
            self.accept()
            async_to_sync(self.channel_layer.group_add)(self.groupID,self.channel_name)
        else:
            self.close()
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.groupID,self.channel_name)
        self.close()
    def receive(self, text_data):
        sender=self.user
        if(sender.is_authenticated):
            data = json.loads(text_data)
            action = data['action']
            messageType = data['messageType']
            messageContent = data['message']
            if(action=='modify'):
                messageID = data.get('messageID')
                message = Message.objects.filter(id=messageID).first()
                owner=message.sender
                changerStatus=Membership.objects.get(group=self.group,user=sender).status
                if(changerStatus=='super' and message.messageType=='joinRequest'):
                    if(messageType=='accept'):
                        membership = Membership.objects.get(user=owner, group=self.group)
                        membership.status='member'
                        membership.save()
                        message.content=messageContent
                        message.messageType='acceptedRequest'
                        message.save()
                    elif(messageType=='reject'):
                        Membership.objects.get(group=self.group,user=owner).delete()
                        message.content = messageContent
                        message.messageType = 'rejectRequest'
                        message.save()
                    async_to_sync(self.channel_layer.group_send)(
                        f'user_{owner.id}',
                        {
                            'type':'onResponse',
                            'groupID':self.groupID,
                            'decision':messageType
                        }
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        self.groupID,
                        {
                            'type': 'onModify',
                            'location':'messageBoard',
                            'action': action,
                            'messageType': message.messageType,
                            'message': {
                                'messageID': messageID,
                                'content': message.content,
                                'time': message.time.strftime("%m/%d/%Y %I:%M %p"),
                            },
                            'owner':{
                                'userID': owner.id,
                                'username': owner.username
                            },
                            'sender': {
                                'userID': sender.id,
                                'username': sender.username
                            }
                        }
                    )
            else:
                message=Message.objects.create(content=messageContent,sender=sender,group_id=self.groupID,messageType='message')
                async_to_sync(self.channel_layer.group_send)(
                    self.groupID,
                    {
                        'type':'onMessage',
                        'location':'messageBoard',
                        'action':action,
                        'messageType':message.messageType,
                        'message': {
                            'messageID': message.id,
                            'content':message.content,
                            'time':message.time.strftime("%m/%d/%Y %I:%M %p")
                        },
                        'sender':{
                            'userID': sender.id,
                            'username': sender.username
                        }
                    }
                )
    def onMessage(self,event):
        del event['type']
        self.send(json.dumps(event))

    def onModify(self,event):
        del event['type']
        self.send(json.dumps(event))

    def onDelete(self,event):
        location=event['location']
        action=event['action']
        messageType=event['messageType']
        message=event.get('message')
        sender=event['sender']
        self.send(json.dumps({
            'location':location,
            'action':action,
            'messageType':messageType,
            'message':{
                'messageID': message.id,
                'content': message.content,
                'time': message.time.strftime("%m/%d/%Y %I:%M %p")
            }
        }))
    def onJoinRequest(self,event):
        location=event['location']
        action = event['action']
        messageType=event['messageType']
        message=event['message']
        sender=event['sender']
        self.send(json.dumps({
            'location': location,
            'action': action,
            'messageType':messageType,
            'message': {
                'messageID':message.id,
                'content': message.content,
                'time': message.time.strftime("%m/%d/%Y %I:%M %p")
            },
            'sender': {
                'userID': sender.id,
                'username': sender.username
            }
        }))
    def onLeave(self,event):
        del event['type']
        self.send(json.dumps(event))
    def onJoin(self,event):
        del event['type']
        self.send(json.dumps(event))



class join(WebsocketConsumer):
    def connect(self):
        self.user=self.scope['user']
        if(self.user.is_authenticated):
            self.accept()
            self.userID=f'user_{self.user.id}'
            async_to_sync(self.channel_layer.group_add)(self.userID,self.channel_name)
        else:
            self.close()
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.userID,self.channel_name)
        self.close()
    def receive(self, text_data=None, bytes_data=None):
        data=json.loads(text_data)
        groupID=data['groupID']
        group=Group.objects.get(id=groupID)
        if(self.user in group.members.all()):
            if(group.membershipTo(self.user)=='pending'):
                joinRequests=Message.objects.filter(sender=self.user,group__id=groupID,messageType='joinRequest').order_by('-time')
                async_to_sync(self.channel_layer.group_send)(
                    groupID,
                    {
                        'type':'onDelete',
                        'location':'messageBoard',
                        'action':'delete',
                        'messageType':'joinRequest',
                        'sender':self.user,
                        'message':joinRequests.first()
                    }
                )
                joinRequests.delete()
            else:
                async_to_sync(self.channel_layer.group_send)(
                    groupID,
                    {
                        'type':'onLeave',
                        'location':'members',
                        'action':'remove',
                        'userID':self.user.id
                    }
                )
            group.members.remove(self.user)
            self.send(json.dumps({'groupID': groupID, 'status': 'removed'}))
        else:
            validRequest=True
            if(group.passwordEnabled=='on'):
                password=data.get('password','')
                validRequest=check_password(password,group.password)
                self.send(json.dumps({'groupID': groupID, 'status': f'password{validRequest}'}))
            if(validRequest):
                if(group.manual=='on'):
                    joinMessage = Message.objects.create(
                        content='Join Request',
                        sender=self.user,
                        group=group,
                        messageType='joinRequest'
                    )
                    group.members.add(self.user, through_defaults={'status': 'pending'})
                    async_to_sync(self.channel_layer.group_send)(
                        groupID,
                        {
                            'type': 'onJoinRequest',
                            'location': 'messageBoard',
                            'action': 'add',
                            'messageType': joinMessage.messageType,
                            'sender': self.user,
                            'message': joinMessage
                        }
                    )
                    self.send(json.dumps({'groupID':groupID,'status':'pending'}))
                else:
                    async_to_sync(self.channel_layer.group_send)(
                        groupID,
                        {
                            'type': 'onJoin',
                            'location':'members',
                            'action':'add',
                            'user':{
                                'userID': self.user.id,
                                'username': self.user.username
                            }
                        }
                    )
                    group.members.add(self.user)
                    self.send(json.dumps({'groupID': groupID, 'status': 'joined'}))
    def onResponse(self,event):
        self.send(json.dumps({'groupID': event['groupID'], 'status': event['decision']}))
