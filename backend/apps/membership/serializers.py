from rest_framework import serializers

from apps.identity.utils.cpf import mascarar_cpf
from apps.membership.models import (
    Coroinha,
    Inscricao,
    SolicitacaoAcesso,
    StatusCoroinha,
    Turma,
)
from apps.membership.utils.media import build_foto_url


class CoroinhaSerializer(serializers.ModelSerializer):
    idade = serializers.IntegerField(read_only=True)
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Coroinha
        fields = (
            "id",
            "nome",
            "data_nascimento",
            "idade",
            "cpf",
            "telefone",
            "endereco",
            "escola",
            "serie",
            "turma",
            "status",
            "batizado",
            "primeira_eucaristia",
            "crisma",
            "foto_url",
            "criado_em",
        )

    def get_foto_url(self, obj):
        return build_foto_url(obj.foto, self.context.get("request"))


class InscricaoPublicaSerializer(serializers.Serializer):
    coroinha = serializers.DictField()
    responsavel = serializers.DictField()

    def validate_coroinha(self, value):
        if not value.get("nome"):
            raise serializers.ValidationError("Nome do coroinha é obrigatório.")
        if not value.get("data_nascimento"):
            raise serializers.ValidationError("Data de nascimento é obrigatória.")
        turma = value.get("turma", Turma.INICIANTE)
        if turma not in dict(Turma.choices):
            value["turma"] = Turma.INICIANTE
        return value

    def validate_responsavel(self, value):
        if not value.get("cpf"):
            raise serializers.ValidationError("CPF do responsável é obrigatório.")
        return value


class InscricaoSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Inscricao
        fields = (
            "id",
            "status",
            "dados",
            "foto_url",
            "criado_em",
            "aprovado_em",
            "coroinha",
            "responsavel",
        )
        read_only_fields = fields

    def get_foto_url(self, obj):
        return build_foto_url(obj.foto_pendente, self.context.get("request"))


class CoroinhaResumoPortalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    idade = serializers.IntegerField()
    escola = serializers.CharField()
    serie = serializers.CharField()
    turma = serializers.CharField()
    status = serializers.CharField()
    foto_url = serializers.CharField(allow_null=True, required=False)
    escalas_total = serializers.IntegerField()
    presencas_total = serializers.IntegerField()
    faltas_total = serializers.IntegerField()
    formacoes_concluidas = serializers.IntegerField()
    formacoes_total = serializers.IntegerField(required=False)
    proxima_escala = serializers.JSONField(allow_null=True)
    escalas = serializers.ListField()
    formacoes = serializers.ListField()


class VerificarAcessoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=200)
    data_nascimento = serializers.DateField()


class CoroinhaVerificadaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    idade = serializers.IntegerField()


class SolicitarAcessoSerializer(serializers.Serializer):
    coroinha_id = serializers.IntegerField()
    nome = serializers.CharField(max_length=200)  # nome do coroinha (reconfirmação)
    data_nascimento = serializers.DateField()
    nome_responsavel = serializers.CharField(max_length=200)
    cpf = serializers.CharField(max_length=14)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    senha = serializers.CharField(min_length=6, write_only=True)
    confirmar_senha = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        if attrs["senha"] != attrs["confirmar_senha"]:
            raise serializers.ValidationError({"confirmar_senha": "As senhas não coincidem."})
        return attrs


class SolicitacaoAcessoSerializer(serializers.ModelSerializer):
    coroinha_nome = serializers.CharField(source="coroinha.nome", read_only=True)
    coroinha_data_nascimento = serializers.DateField(
        source="coroinha.data_nascimento", read_only=True
    )
    cpf_mascarado = serializers.SerializerMethodField()

    class Meta:
        model = SolicitacaoAcesso
        fields = (
            "id",
            "coroinha",
            "coroinha_nome",
            "coroinha_data_nascimento",
            "nome_responsavel",
            "cpf_mascarado",
            "whatsapp",
            "status",
            "criado_em",
            "processado_em",
        )
        read_only_fields = fields

    def get_cpf_mascarado(self, obj):
        return mascarar_cpf(obj.cpf)


class AniversarianteSerializer(serializers.ModelSerializer):
    idade = serializers.IntegerField(read_only=True)
    foto_url = serializers.SerializerMethodField()
    dia = serializers.SerializerMethodField()

    class Meta:
        model = Coroinha
        fields = ("id", "nome", "data_nascimento", "idade", "dia", "foto_url", "turma")

    def get_foto_url(self, obj):
        return build_foto_url(obj.foto, self.context.get("request"))

    def get_dia(self, obj):
        return obj.data_nascimento.day
