from django.db import models


class DiaSemana(models.TextChoices):
    DOMINGO = "Domingo", "Domingo"
    SEGUNDA = "Segunda", "Segunda"
    TERCA = "Terca", "Terça"
    QUARTA = "Quarta", "Quarta"
    QUINTA = "Quinta", "Quinta"
    SEXTA = "Sexta", "Sexta"
    SABADO = "Sabado", "Sábado"


class ModoEscala(models.TextChoices):
    SORTEIO_AUTOMATICO = "SorteioAutomatico", "Sorteio automático"
    SELECAO_MANUAL = "SelecaoManual", "Seleção manual"
    GRUPO_MENSAL = "GrupoMensal", "Grupo mensal"


class TipoSlotMissa(models.TextChoices):
    SABADO_NOITE = "SabadoNoite", "Sábado noite"
    DOMINGO_MANHA = "DomingoManha", "Domingo manhã"
    DOMINGO_NOITE = "DomingoNoite", "Domingo noite"
    SEXTA_ADORACAO = "SextaAdoracao", "Sexta — Adoração + Missa"
    QUARTA_VOLUNTARIOS = "QuartaVoluntarios", "Quarta — Voluntários"
    DIA_13 = "Dia13", "Dia 13"
    COMUNIDADE_DOMINGO = "ComunidadeDomingo", "Comunidade — Domingo"
    OUTRO = "Outro", "Outro"


class LocalCelebracao(models.TextChoices):
    SANTUARIO = "Santuario", "Santuário de Fátima"
    COMUNIDADE = "Comunidade", "Comunidade Santo Antônio"


class FuncaoEscala(models.TextChoices):
    CRUZ = "Cruz", "Cruz"
    VELA_1 = "Vela1", "Vela 1"
    VELA_2 = "Vela2", "Vela 2"
    TURIBULO = "Turibulo", "Turíbulo"
    NAVETA = "Naveta", "Naveta"
    MISSAL = "Missal", "Missal"
    ENTRE_OS_DOIS = "EntreOsDois", "Entre os dois"
    OFERTORIO = "Ofertorio", "Ofertório"
    ASSESSOR = "Assessor", "Assessor"


FUNCOES_ESCALA_ORDEM = [
    FuncaoEscala.CRUZ,
    FuncaoEscala.VELA_1,
    FuncaoEscala.VELA_2,
    FuncaoEscala.TURIBULO,
    FuncaoEscala.NAVETA,
    FuncaoEscala.MISSAL,
    FuncaoEscala.ENTRE_OS_DOIS,
    FuncaoEscala.OFERTORIO,
    FuncaoEscala.ASSESSOR,
]


class Missa(models.Model):
    nome = models.CharField(max_length=100)
    dia_semana = models.CharField(max_length=20, choices=DiaSemana.choices, blank=True, null=True)
    dia_mes = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Dia do mês (ex.: 13) para missas mensais fixas.",
    )
    horario = models.TimeField()
    ativa = models.BooleanField(default=True)
    tipo_slot = models.CharField(
        max_length=30,
        choices=TipoSlotMissa.choices,
        default=TipoSlotMissa.OUTRO,
    )
    local = models.CharField(
        max_length=30,
        choices=LocalCelebracao.choices,
        default=LocalCelebracao.SANTUARIO,
    )

    class Meta:
        verbose_name = "Missa"
        verbose_name_plural = "Missas"
        ordering = ["dia_mes", "dia_semana", "horario"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(dia_semana__isnull=False) | models.Q(dia_mes__isnull=False),
                name="missa_dia_semana_ou_dia_mes",
            ),
        ]

    def __str__(self):
        return self.nome

    @property
    def recorrencia(self) -> str:
        if self.dia_mes:
            return f"Dia {self.dia_mes} do mês"
        return self.get_dia_semana_display() or ""


class EscalaMensal(models.Model):
    """Planejamento de escalas de um mês — grupos renovados a cada geração."""

    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    tamanho_grupo = models.PositiveSmallIntegerField(default=9)
    quantidade_sexta = models.PositiveSmallIntegerField(default=2)
    quantidade_comunidade = models.PositiveSmallIntegerField(default=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        "identity.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="escalas_mensais_criadas",
    )

    class Meta:
        verbose_name = "Escala mensal"
        verbose_name_plural = "Escalas mensais"
        ordering = ["-ano", "-mes"]
        unique_together = [("ano", "mes")]

    def __str__(self):
        return f"Escala {self.mes:02d}/{self.ano}"


class GrupoMensal(models.Model):
    escala_mensal = models.ForeignKey(
        EscalaMensal, on_delete=models.CASCADE, related_name="grupos"
    )
    numero = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["numero"]
        unique_together = [("escala_mensal", "numero")]

    def __str__(self):
        return f"Grupo {self.numero} — {self.escala_mensal}"


class GrupoMensalMembro(models.Model):
    grupo = models.ForeignKey(GrupoMensal, on_delete=models.CASCADE, related_name="membros")
    coroinha = models.ForeignKey(
        "membership.Coroinha", on_delete=models.CASCADE, related_name="grupos_mensais"
    )
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordem"]
        unique_together = [("grupo", "coroinha")]


class Escala(models.Model):
    data = models.DateField()
    missa = models.ForeignKey(Missa, on_delete=models.PROTECT, related_name="escalas")
    modo = models.CharField(max_length=20, choices=ModoEscala.choices)
    escala_mensal = models.ForeignKey(
        EscalaMensal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="escalas",
    )
    grupo_numero = models.PositiveSmallIntegerField(null=True, blank=True)
    observacao = models.TextField(blank=True)
    voluntarios = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        "identity.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="escalas_criadas",
    )

    class Meta:
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        ordering = ["-data", "missa__horario"]
        unique_together = [("data", "missa")]

    def __str__(self):
        return f"{self.data} — {self.missa.nome}"


class EscalaItem(models.Model):
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE, related_name="itens")
    coroinha = models.ForeignKey(
        "membership.Coroinha", on_delete=models.CASCADE, related_name="escala_itens"
    )
    ordem = models.PositiveSmallIntegerField(default=0)
    funcao = models.CharField(
        max_length=20,
        choices=FuncaoEscala.choices,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Item da escala"
        ordering = ["ordem", "coroinha__nome"]
        unique_together = [("escala", "coroinha")]
        constraints = [
            models.UniqueConstraint(
                fields=["escala", "funcao"],
                condition=models.Q(funcao__isnull=False),
                name="escala_funcao_unica",
            ),
        ]

    def __str__(self):
        sufixo = f" ({self.get_funcao_display()})" if self.funcao else ""
        return f"{self.escala} — {self.coroinha.nome}{sufixo}"
