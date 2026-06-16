import json
from datetime import date, datetime, time
from pathlib import Path

from django.utils import timezone

from apps.content.models import Noticia
from apps.training.models import Formacao

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_ARQUIVO = DATA_DIR / "calendario_paroquial_2026_coroinhas.json"


def _parse_data(valor: date | str | None) -> date | None:
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(valor)


def _chave_importacao(evento: dict) -> str:
    return evento.get("id") or f"{evento['tipo']}-{evento['data']}-{evento['titulo']}"


def _descricao_publica(evento: dict) -> str:
    return evento.get("descricao", "").strip()


def _descricao_formacao(evento: dict) -> str:
    partes = []
    if evento.get("local"):
        partes.append(f"Local: {evento['local']}")
    if evento.get("horario"):
        partes.append(f"Horário: {evento['horario']}")
    descricao = _descricao_publica(evento)
    if partes:
        partes.append("")
    if descricao:
        partes.append(descricao)
    return "\n".join(partes).strip()


class CalendarioImportService:
    @classmethod
    def carregar_arquivo(cls, caminho: Path | None = None) -> dict:
        path = caminho or DEFAULT_ARQUIVO
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def importar(
        cls,
        caminho: Path | None = None,
        autor=None,
        dry_run: bool = False,
    ) -> dict:
        payload = cls.carregar_arquivo(caminho)
        stats = {
            "noticias_criadas": 0,
            "noticias_atualizadas": 0,
            "formacoes_criadas": 0,
            "formacoes_atualizadas": 0,
            "noticias_legadas_removidas": 0,
        }

        if not dry_run:
            removidas, _ = Noticia.objects.filter(
                conteudo__contains="[calendario-paroquial]",
                referencia_calendario__isnull=True,
            ).delete()
            stats["noticias_legadas_removidas"] = removidas

        for bruto in payload.get("eventos", []):
            evento = {**bruto, "_chave": _chave_importacao(bruto)}
            if evento["tipo"] == "formacao":
                cls._importar_formacao(evento, stats, dry_run)
            elif evento["tipo"] == "noticia":
                cls._importar_noticia(evento, stats, autor, dry_run)
        return stats

    @classmethod
    def _importar_formacao(cls, evento: dict, stats: dict, dry_run: bool) -> None:
        titulo = evento["titulo"]
        data_ev = _parse_data(evento["data"])
        descricao = _descricao_formacao(evento)
        if dry_run:
            stats["formacoes_criadas"] += 1
            return

        _, created = Formacao.objects.update_or_create(
            titulo=titulo,
            data=data_ev,
            defaults={"descricao": descricao},
        )
        if created:
            stats["formacoes_criadas"] += 1
        else:
            stats["formacoes_atualizadas"] += 1

    @classmethod
    def _importar_noticia(cls, evento: dict, stats: dict, autor, dry_run: bool) -> None:
        chave = evento["_chave"]
        data_ev = _parse_data(evento["data"])
        data_fim = _parse_data(evento.get("data_fim"))
        if data_fim == data_ev:
            data_fim = None

        defaults = {
            "titulo": evento["titulo"],
            "conteudo": _descricao_publica(evento),
            "data_evento": data_ev,
            "data_evento_fim": data_fim,
            "local_evento": evento.get("local") or "",
            "horario_evento": evento.get("horario") or "",
            "destaque": bool(evento.get("destaque", False)),
            "ativo": True,
        }
        if autor:
            defaults["autor"] = autor

        if dry_run:
            stats["noticias_criadas"] += 1
            return

        noticia, created = Noticia.objects.update_or_create(
            referencia_calendario=chave,
            defaults=defaults,
        )
        if data_ev:
            publicado_em = timezone.make_aware(
                datetime.combine(data_ev, time(12, 0)),
                timezone.get_current_timezone(),
            )
            Noticia.objects.filter(pk=noticia.pk).update(publicado_em=publicado_em)

        if created:
            stats["noticias_criadas"] += 1
        else:
            stats["noticias_atualizadas"] += 1
