from rest_framework import serializers

from apps.membership.models import Coroinha, Inscricao, StatusCoroinha, Turma
from apps.membership.utils.media import build_foto_url


class CoroinhaSerializer(serializers.ModelSerializer):
    idade = serializers.IntegerField(read_only=True)
    foto = serializers.ImageField(write_only=True, required=False, allow_null=True)
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
            "nome_pai",
            "telefone_pai",
            "nome_mae",
            "telefone_mae",
            "escola",
            "serie",
            "turma",
            "status",
            "faz_catequese",
            "etapa_catequese",
            "faz_iam",
            "antigo",
            "batizado",
            "primeira_eucaristia",
            "crisma",
            "foto",
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
        # CPF do responsável é opcional: quando informado, habilita o acesso
        # da família ao portal; quando ausente, os dados dos pais ficam
        # registrados apenas no coroinha.
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
