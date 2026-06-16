from django.contrib import admin

from .models import AuditLog, TipoPerfil, Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_perfil", "email", "cpf", "is_active", "must_change_password")
    list_filter = ("tipo_perfil", "is_active")
    search_fields = ("nome", "email", "cpf")
    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        (None, {"fields": ("nome", "tipo_perfil", "email", "cpf", "password")}),
        ("Vínculos", {"fields": ("coroinha", "responsavel")}),
        ("Status", {"fields": ("must_change_password", "is_active", "is_staff", "is_superuser")}),
        ("Datas", {"fields": ("criado_em", "atualizado_em")}),
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.tipo_perfil == TipoPerfil.COORDENADOR:
            obj.is_staff = True
        super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("acao", "usuario", "ip", "criado_em")
    list_filter = ("acao",)
    search_fields = ("usuario__nome", "ip")
    readonly_fields = ("acao", "usuario", "ip", "detalhes", "criado_em")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
