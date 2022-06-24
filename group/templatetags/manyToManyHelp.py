from django import template
from ..models import User,Group,Message,Membership

register = template.Library()


memberships=Membership.objects.all()

@register.filter
def membershipStatus(group,userID):
    membership=memberships.filter(group=group,user__id=userID).first()
    if(membership):
        return membership.status
    else:
        return None