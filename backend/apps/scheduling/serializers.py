from rest_framework import serializers

from apps.communication.models import CanalMensagem
from apps.scheduling.models import (
    Escala,
    EscalaItem,
    EscalaMensal,
    GrupoMensal,
    GrupoMensalMembro,
    Missa,
    ModoEscala,
    FuncaoEscala,
    TipoSlotMissa,
)


class MissaSerializer(serializers.ModelSerializer):
    recorrencia = serializers.CharField(read_only=True)

    class Meta:
        model = Missa
        fields = ("id", "nome", "dia_semana", "dia_mes", "horario", "ativa", "recorrencia", "tipo_slot")
        read_only_fields = ("tipo_slot",)

    def validate(self, attrs):
        dia_semana = attrs.get("dia_semana", getattr(self.instance, "dia_semana", None))
        dia_mes = attrs.get("dia_mes", getattr(self.instance, "dia_mes", None))
        if self.partial:
            if "dia_semana" in attrs and attrs["dia_semana"] and dia_mes:
                attrs["dia_mes"] = None
            if "dia_mes" in attrs and attrs["dia_mes"] and dia_semana:
                attrs["dia_semana"] = None
            dia_semana = attrs.get("dia_semana", getattr(self.instance, "dia_semana", None))
            dia_mes = attrs.get("dia_mes", getattr(self.instance, "dia_mes", None))
        if not dia_semana and not dia_mes:
            raise serializers.ValidationError("Informe o dia da semana ou o dia do mês.")
        if dia_semana and dia_mes:
            raise serializers.ValidationError("Use dia da semana ou dia do mês, não ambos.")
        if dia_mes is not None and not (1 <= dia_mes <= 31):
            raise serializers.ValidationError({"dia_mes": "Dia do mês deve ser entre 1 e 31."})
        if dia_mes == 13:
            attrs["tipo_slot"] = TipoSlotMissa.DIA_13
        return attrs

    def create(self, validated_data):
        if validated_data.get("dia_mes"):
            validated_data["dia_semana"] = None
        else:
            validated_data["dia_mes"] = None
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("dia_mes"):
            validated_data["dia_semana"] = None
        elif validated_data.get("dia_semana"):
            validated_data["dia_mes"] = None
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["recorrencia"] = instance.recorrencia
        return data


from apps.membership.utils.media import build_foto_url


class EscalaItemSerializer(serializers.ModelSerializer):
    coroinha_nome = serializers.CharField(source="coroinha.nome", read_only=True)
    coroinha_id = serializers.IntegerField(source="coroinha.id", read_only=True)
    coroinha_foto_url = serializers.SerializerMethodField()
    presenca_status = serializers.SerializerMethodField()
    funcao_label = serializers.SerializerMethodField()

    class Meta:
        model = EscalaItem
        fields = (
            "id",
            "coroinha_id",
            "coroinha_nome",
            "coroinha_foto_url",
            "ordem",
            "funcao",
            "funcao_label",
            "presenca_status",
        )

    def get_funcao_label(self, obj):
        return obj.get_funcao_display() if obj.funcao else None

    def get_coroinha_foto_url(self, obj):
        return build_foto_url(obj.coroinha.foto, self.context.get("request"))

    def get_presenca_status(self, obj):
        try:
            return obj.presenca.status
        except Exception:
            return None


class EscalaSerializer(serializers.ModelSerializer):
    missa_nome = serializers.CharField(source="missa.nome", read_only=True)
    missa_horario = serializers.TimeField(source="missa.horario", format="%H:%M", read_only=True)
    missa_tipo_slot = serializers.CharField(source="missa.tipo_slot", read_only=True)
    missa_dia_mes = serializers.IntegerField(source="missa.dia_mes", read_only=True)
    missa_local = serializers.CharField(source="missa.local", read_only=True)
    itens = EscalaItemSerializer(many=True, read_only=True)
    notificacao_enviada = serializers.SerializerMethodField()

    class Meta:
        model = Escala
        fields = (
            "id",
            "data",
            "missa",
            "missa_nome",
            "missa_horario",
            "missa_tipo_slot",
            "missa_dia_mes",
            "missa_local",
            "modo",
            "criado_em",
            "itens",
            "notificacao_enviada",
            "grupo_numero",
            "observacao",
            "voluntarios",
        )

    def get_notificacao_enviada(self, obj):
        return obj.mensagens_notificacao.exists()


class MontarEscalaSerializer(serializers.Serializer):
    data = serializers.DateField()
    missa_id = serializers.IntegerField()
    modo = serializers.ChoiceField(choices=ModoEscala.choices)
    quantidade = serializers.IntegerField(min_value=1, max_value=20)
    coroinha_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    funcoes = serializers.DictField(child=serializers.IntegerField(), required=False, allow_empty=True)
    notificar = serializers.BooleanField(required=False, default=None, allow_null=True)

    def validate_funcoes(self, value):
        validas = {c.value for c in FuncaoEscala}
        for chave in value:
            if chave not in validas:
                raise serializers.ValidationError(f"Função inválida: {chave}")
        return value

    def validate(self, attrs):
        if attrs["modo"] == ModoEscala.SELECAO_MANUAL and not attrs.get("coroinha_ids"):
            raise serializers.ValidationError({"coroinha_ids": "Obrigatório para seleção manual."})
        return attrs


class NotificarEscalaSerializer(serializers.Serializer):
    canal = serializers.ChoiceField(choices=CanalMensagem.choices, required=False)


class AtribuirFuncoesSerializer(serializers.Serializer):
    funcoes = serializers.DictField(child=serializers.IntegerField(allow_null=True), allow_empty=True)

    def validate_funcoes(self, value):
        validas = {c.value for c in FuncaoEscala}
        for chave in value:
            if chave not in validas:
                raise serializers.ValidationError(f"Função inválida: {chave}")
        return value


class DefinirMembrosSerializer(serializers.Serializer):
    coroinha_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class RemanejarGrupoSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2020, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)
    coroinha_id = serializers.IntegerField()
    grupo_destino = serializers.IntegerField(min_value=1, max_value=4)


class RemoverGrupoSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2020, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)
    coroinha_id = serializers.IntegerField()


class MoverCoroinhaCelebracaoSerializer(serializers.Serializer):
    coroinha_id = serializers.IntegerField()
    escala_destino_id = serializers.IntegerField(required=False, allow_null=True)


class TransferirCelebracaoSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2020, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)
    coroinha_id = serializers.IntegerField()
    escala_destino_id = serializers.IntegerField()
    grupo_numero = serializers.IntegerField(min_value=1, max_value=4, required=False, allow_null=True)


class AtribuirGrupoCelebracaoSerializer(serializers.Serializer):
    grupo_numero = serializers.IntegerField(min_value=1, max_value=4)


class GrupoMensalMembroSerializer(serializers.ModelSerializer):
    coroinha_id = serializers.IntegerField(source="coroinha.id", read_only=True)
    coroinha_nome = serializers.CharField(source="coroinha.nome", read_only=True)

    class Meta:
        model = GrupoMensalMembro
        fields = ("coroinha_id", "coroinha_nome", "ordem")


class GrupoMensalSerializer(serializers.ModelSerializer):
    membros = GrupoMensalMembroSerializer(many=True, read_only=True)

    class Meta:
        model = GrupoMensal
        fields = ("numero", "membros")


class EscalaMensalSerializer(serializers.ModelSerializer):
    grupos = GrupoMensalSerializer(many=True, read_only=True)
    total_escalas = serializers.SerializerMethodField()

    class Meta:
        model = EscalaMensal
        fields = (
            "id",
            "ano",
            "mes",
            "tamanho_grupo",
            "quantidade_sexta",
            "quantidade_comunidade",
            "criado_em",
            "grupos",
            "total_escalas",
        )

    def get_total_escalas(self, obj):
        return obj.escalas.count()


class GerarEscalaMesSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2020, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)
    tamanho_grupo = serializers.IntegerField(min_value=4, max_value=15, default=9)
    quantidade_sexta = serializers.IntegerField(min_value=1, max_value=6, default=2)
    quantidade_comunidade = serializers.IntegerField(min_value=1, max_value=6, default=2)
    substituir = serializers.BooleanField(default=False)
