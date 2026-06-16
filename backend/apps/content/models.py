from django.db import models


class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    data_evento = models.DateField(blank=True, null=True)
    data_evento_fim = models.DateField(blank=True, null=True)
    local_evento = models.CharField(max_length=200, blank=True)
    horario_evento = models.CharField(max_length=100, blank=True)
    referencia_calendario = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        unique=True,
        help_text="ID estável para importação do calendário paroquial.",
    )
    destaque = models.BooleanField(default=False)
    publicado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    autor = models.ForeignKey(
        "identity.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="noticias",
    )

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ["-publicado_em"]

    def __str__(self):
        return self.titulo


class CategoriaDocumento(models.TextChoices):
    LITURGIA = "Liturgia", "Liturgia"
    FORMACAO = "Formacao", "Formação"
    RITUAL = "Ritual", "Ritual"
    OUTRO = "Outro", "Outro"


class Documento(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    url = models.URLField(blank=True)
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaDocumento.choices,
        default=CategoriaDocumento.OUTRO,
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo
