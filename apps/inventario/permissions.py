from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

ROLE_ADMIN = 'Administrador'
ROLE_VENDEDOR = 'Vendedor'
ROLE_BODEGUERO = 'Bodeguero'


def user_in_groups(user, *group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Modo compatibilidad: si el usuario no tiene grupos asignados, se permite acceso
    # para no romper instalaciones existentes antes de ejecutar `seed_roles`.
    if not user.groups.exists():
        return True
    return user.groups.filter(name__in=group_names).exists()


def role_required(*group_names):
    """Decorator para permitir acceso solo a roles/grupos específicos."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if user_in_groups(request.user, *group_names):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('No tienes permisos para acceder a esta sección.')

        return _wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_groups = tuple()

    def dispatch(self, request, *args, **kwargs):
        if user_in_groups(request.user, *self.allowed_groups):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied('No tienes permisos para acceder a esta sección.')
