from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password,check_password
from django.core.validators import validate_image_file_extension
from django.core.files import File
import re,os
# Create your models here.


class User(AbstractUser):
    profileImage=models.ImageField(
        upload_to=os.path.join('profilePicture',os.environ.get('DEVELOPMENT','production')),
        default=os.path.join('profilePicture','default.PNG'),
        validators=[validate_image_file_extension]
    )

    def setImage(self,imageFile):
        imageFile.name = re.sub(r".+(?=\.)", str(self.id), imageFile.name)
        self.profileImage=imageFile

    def encrypt(self):
        if (self.password!=None):
            user = User.objects.filter(id=self.id).first()
            if (user and user.password):
                if (check_password(self.password, user.password)):
                    self.password = user.password
                else:
                    self.password = make_password(self.password)
            else:
                self.password = make_password(self.password)

class Group(models.Model):
    name=models.TextField()
    description=models.TextField(blank=True,null=True)
    backgroundEnabled=models.TextField(default='off')
    background=models.URLField(blank=True,null=True)
    passwordEnabled=models.TextField(default='off')
    password = models.TextField(blank=True,null=True)
    private=models.TextField(blank=True)
    manual=models.TextField(blank=True)
    members = models.ManyToManyField('User',through='Membership',related_name='group')


    def __str__(self):
        return self.name
    def membershipTo(self,user):
        membership=Membership.objects.filter(group=self,user=user).first()
        if(membership):
            return membership.status
        return membership
    def encrypt(self):
        if (self.password!=None):
            group = Group.objects.filter(id=self.id).first()
            if (group and group.password):
                if (check_password(self.password, group.password)):
                    self.password = group.password
                else:
                    self.password = make_password(self.password)
            else:
                self.password = make_password(self.password)

class Message(models.Model):
    messageType=models.TextField()
    content=models.TextField()
    sender=models.ForeignKey(User,on_delete=models.CASCADE,related_name='messages')
    group=models.ForeignKey(Group,on_delete=models.CASCADE,related_name='messages')
    time=models.DateTimeField(auto_now_add=True)

class Membership(models.Model):
    group=models.ForeignKey(Group,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    status=models.TextField(default='member')