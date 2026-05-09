from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    if not user.groups.exists():
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter
def has_any_group(user, group_names):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    if not user.groups.exists():
        return True
    names = [name.strip() for name in str(group_names).split(',') if name.strip()]
    return user.groups.filter(name__in=names).exists()
