import json
import re
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.urls import reverse
from django.contrib.auth import logout,login,authenticate,hashers
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import User,Group,Message,Membership
from django.core.files import File
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
# Create your views here.

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "group/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "group/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "group/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(request, "group/register.html", {
                "message": "Username already taken."
            })
        profileImage = request.FILES.get('profileImage')
        if(profileImage):
            user.setImage(profileImage)
        user.save()

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "group/register.html")

def index(request):
    return render(request,'group/index.html',{'all':Group.objects.all()})


def personal(request):
    userID=request.GET.get('userID')
    user = User.objects.filter(id=userID).first()
    if(user):
        return render(request, 'group/index.html', {
            'profile':user,
            'super': user.group.filter(membership__status='super'),
            'member': user.group.filter(membership__status='member'),
            'pending':user.group.filter(membership__status='pending'),
            'nonMember': Group.objects.all().difference(user.group.all())
        })
    else:
        return HttpResponse('User does not exist')
def group(request,groupID):
    if(request.method=='GET'):
        group=Group.objects.get(id=groupID)
        if(group.private=='off' or (request.user.is_authenticated and group in request.user.group.all())):
            return render(request,'group/group.html',{
                'group':group,
                'members':group.members.filter(membership__status='member'),
                'supers':group.members.filter(membership__status='super')
            })
        return HttpResponseNotFound("You don't have access to such group")

    else:
        return JsonResponse({'error':'only get method allowed'})
@login_required
def create(request):
    if(request.method=='POST'):
        postParam=request.POST
        name=postParam.get('name')
        if(Group.objects.filter(name=name)):
            return render(request, 'group/create.html',{'message':'group name already exist'})
        description=postParam.get('description')
        backgroundEnabled=postParam.get('backgroundCheckBox','off')
        background=postParam.get('background')
        passwordEnabled=postParam.get('passwordCheckBox','off')
        password=postParam.get('password')
        private=postParam.get('privateCheckBox','off')
        manual=postParam.get('manualCheckBox','off')
        group=Group(
            name=name,
            description=description,
            backgroundEnabled=backgroundEnabled,
            background=background,
            passwordEnabled=passwordEnabled,
            password=password,
            private=private,
            manual=manual
        )
        group.encrypt()
        group.save()
        Membership(group=group,user=request.user,status='super').save()
        return HttpResponseRedirect(reverse('index'))
    return render(request,'group/create.html')


def search(request):
    if(request.method=='GET'):
        searchParam=request.GET.get('filter','')
        return render(request,'group/index.html',{'all':Group.objects.filter(name__icontains=searchParam)})
    return JsonResponse({'error':'api only accept GET'},status=400)


def messages(request):
    if(request.method=='GET'):
        groupID=request.GET['groupID']
        group=Group.objects.get(id=groupID)
        if(request.user in group.members.all() or group.private=='off'):
            messages=Message.objects.filter(group=group)
            def createAPI(data):
                api=[]
                for message in data:
                    api.append({
                        'messageType':message.messageType,
                        'message': {
                            'messageID':message.id,
                            'content':message.content,
                            'time':message.time.strftime("%m/%d/%Y %I:%M %p")
                        },
                        'sender':{
                            'userID':message.sender.id,
                            'username':message.sender.username
                        }
                    })
                return api
            return JsonResponse(createAPI(messages),status=200,safe=False)
        else:
            return JsonResponse({'error':"You don't have access to the api"},status=400)
    else:
        return JsonResponse({'error':'API only accept GET request'},status=400)

@login_required
def modifySetting(request,groupID):
    if(request.method=='POST'):
        group=Group.objects.get(id=groupID)
        data=json.loads(request.body)
        group.name=data.get('name')
        group.description=data.get('description')
        group.backgroundEnabled=data.get('backgroundCheckBox','off')
        group.background=data.get('background')
        group.private=data.get('privateCheckBox','off')
        group.manual=data.get('manualCheckBox','off')
        group.passwordEnabled=data.get('passwordCheckBox','off')
        if(data.get('newPasswordCheckBox','off')=='on'):
            group.password=data.get('newPassword')
            group.encrypt()
        group.save()
        return JsonResponse({'sucess':data},status=200)
    else:
        return JsonResponse({'error':'api only accept POST request'},status=400)

@login_required
def editProfile(request):
    if(request.user.is_authenticated):
        if(request.method=='POST'):
            user=request.user
            username=request.POST['username']
            email=request.POST['email']
            newPasswordCheckBox=request.POST.get('newPasswordCheckBox','off')
            newPassword=request.POST.get('newPassword')
            newConfirmation=request.POST.get('newConfirmation')
            profileImage=request.FILES.get('profileImage')

            user.username=username
            user.email=email
            if(newPasswordCheckBox=='on'):
                if(newPassword==newConfirmation):
                    user.password=newPassword
                    user.encrypt()
                else:
                    return render(request, 'group/editProfile.html',{'message':'confirmation do not match password'})
            if(profileImage):
                user.setImage(profileImage)
            user.save()
            login(request,user)
            return HttpResponseRedirect(f"{reverse('personal')}?userID={user.id}")
        return render(request,'group/editProfile.html')
    else:
        return HttpResponse('You Are Not Logged In',status=400)
