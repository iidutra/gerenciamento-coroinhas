from rest_framework import serializers

from apps.identity.models import TipoPerfil, Usuario

STAFF_PERFIS = (TipoPerfil.COORDENADOR, TipoPerfil.SECRETARIO, TipoPerfil.PADRE)


class UsuarioStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "nome", "email", "tipo_perfil", "is_active")
        read_only_fields = ("id",)


class CriarUsuarioStaffSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    tipo_perfil = serializers.ChoiceField(choices=[p.value for p in STAFF_PERFIS if p != TipoPerfil.COORDENADOR])
    senha = serializers.CharField(min_length=6, write_only=True)

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return value.lower()


class AtualizarUsuarioStaffSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=200, required=False)
    tipo_perfil = serializers.ChoiceField(
        choices=[p.value for p in STAFF_PERFIS if p != TipoPerfil.COORDENADOR],
        required=False,
    )
    is_active = serializers.BooleanField(required=False)
    senha = serializers.CharField(min_length=6, write_only=True, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Informe ao menos um campo.")
        return attrs
