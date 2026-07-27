"""Gera escalas de um mês inteiro com grupos rotativos."""

import calendar
from datetime import date, timedelta

from django.db import transaction

from apps.membership.models import Coroinha, StatusCoroinha
from apps.scheduling.models import (
    Escala,
    EscalaItem,
    EscalaMensal,
    GrupoMensal,
    GrupoMensalMembro,
    LocalCelebracao,
    Missa,
    ModoEscala,
    TipoSlotMissa,
)
from apps.scheduling.services.grupo_montagem_service import (
    ROTACAO_FIM_DE_SEMANA,
    GrupoMontagemService,
)

OBS_SEXTA = "Adoração ao Santíssimo seguida de Missa"
OBS_QUARTA = "Voluntários"


class GeradorEscalaMensalService:
    @classmethod
    @transaction.atomic
    def gerar(
        cls,
        *,
        ano: int,
        mes: int,
        usuario,
        tamanho_grupo: int = 9,
        quantidade_sexta: int = 2,
        quantidade_comunidade: int = 2,
        substituir: bool = False,
    ) -> EscalaMensal:
        if not (1 <= mes <= 12):
            raise ValueError("Mês inválido.")

        existente = EscalaMensal.objects.filter(ano=ano, mes=mes).first()
        if existente and not substituir:
            raise ValueError(f"Já existe escala mensal para {mes:02d}/{ano}. Use substituir=true.")
        if existente and substituir:
            existente.escalas.all().delete()
            existente.delete()

        grupos_map = GrupoMontagemService.montar_grupos(tamanho_grupo)

        escala_mensal = EscalaMensal.objects.create(
            ano=ano,
            mes=mes,
            tamanho_grupo=tamanho_grupo,
            quantidade_sexta=quantidade_sexta,
            quantidade_comunidade=quantidade_comunidade,
            criado_por=usuario,
        )

        grupos_db: dict[int, GrupoMensal] = {}
        for numero, membros in grupos_map.items():
            grupo = GrupoMensal.objects.create(escala_mensal=escala_mensal, numero=numero)
            grupos_db[numero] = grupo
            for ordem, coroinha in enumerate(membros, start=1):
                GrupoMensalMembro.objects.create(grupo=grupo, coroinha=coroinha, ordem=ordem)

        missas = {m.tipo_slot: m for m in Missa.objects.filter(ativa=True) if m.tipo_slot}
        _, ultimo_dia = calendar.monthrange(ano, mes)
        datas = [date(ano, mes, d) for d in range(1, ultimo_dia + 1)]

        cls._gerar_fins_de_semana(datas, escala_mensal, grupos_map, missas, usuario)
        cls._gerar_sextas(datas, escala_mensal, missas, usuario, quantidade_sexta, grupos_map)
        cls._gerar_quartas(datas, escala_mensal, missas, usuario)
        cls._gerar_comunidade(datas, escala_mensal, missas, usuario, quantidade_comunidade)

        return escala_mensal

    @classmethod
    def _criar_escala_com_membros(
        cls,
        *,
        data: date,
        missa: Missa,
        usuario,
        escala_mensal: EscalaMensal,
        coroinhas: list[Coroinha],
        grupo_numero: int | None = None,
        observacao: str = "",
        voluntarios: bool = False,
    ) -> Escala | None:
        if Escala.objects.filter(data=data, missa=missa).exists():
            return None

        escala = Escala.objects.create(
            data=data,
            missa=missa,
            modo=ModoEscala.GRUPO_MENSAL if coroinhas else ModoEscala.SORTEIO_AUTOMATICO,
            criado_por=usuario,
            escala_mensal=escala_mensal,
            grupo_numero=grupo_numero,
            observacao=observacao,
            voluntarios=voluntarios,
        )
        for ordem, coroinha in enumerate(coroinhas, start=1):
            EscalaItem.objects.create(escala=escala, coroinha=coroinha, ordem=ordem)
        return escala

    @classmethod
    def _gerar_fins_de_semana(cls, datas, escala_mensal, grupos_map, missas, usuario):
        missa_sab = missas.get(TipoSlotMissa.SABADO_NOITE)
        missa_dom_m = missas.get(TipoSlotMissa.DOMINGO_MANHA)
        missa_dom_n = missas.get(TipoSlotMissa.DOMINGO_NOITE)
        if not (missa_sab and missa_dom_m and missa_dom_n):
            return

        sabados = [d for d in datas if d.weekday() == 5]
        for i, sab in enumerate(sabados):
            rot = ROTACAO_FIM_DE_SEMANA[i % len(ROTACAO_FIM_DE_SEMANA)]
            cls._criar_escala_com_membros(
                data=sab,
                missa=missa_sab,
                usuario=usuario,
                escala_mensal=escala_mensal,
                coroinhas=list(grupos_map.get(rot["sabado"], [])),
                grupo_numero=rot["sabado"],
            )
            dom = sab + timedelta(days=1)
            if dom.month == sab.month:
                cls._criar_escala_com_membros(
                    data=dom,
                    missa=missa_dom_m,
                    usuario=usuario,
                    escala_mensal=escala_mensal,
                    coroinhas=list(grupos_map.get(rot["dom_manha"], [])),
                    grupo_numero=rot["dom_manha"],
                )
                cls._criar_escala_com_membros(
                    data=dom,
                    missa=missa_dom_n,
                    usuario=usuario,
                    escala_mensal=escala_mensal,
                    coroinhas=list(grupos_map.get(rot["dom_noite"], [])),
                    grupo_numero=rot["dom_noite"],
                )

        if sabados:
            first_sat = sabados[0]
            for d in datas:
                if d.weekday() == 6 and d < first_sat:
                    rot = ROTACAO_FIM_DE_SEMANA[0]
                    cls._criar_escala_com_membros(
                        data=d,
                        missa=missa_dom_m,
                        usuario=usuario,
                        escala_mensal=escala_mensal,
                        coroinhas=list(grupos_map.get(rot["dom_manha"], [])),
                        grupo_numero=rot["dom_manha"],
                    )
                    cls._criar_escala_com_membros(
                        data=d,
                        missa=missa_dom_n,
                        usuario=usuario,
                        escala_mensal=escala_mensal,
                        coroinhas=list(grupos_map.get(rot["dom_noite"], [])),
                        grupo_numero=rot["dom_noite"],
                    )

    @classmethod
    def _gerar_sextas(cls, datas, escala_mensal, missas, usuario, quantidade, grupos_map):
        missa = missas.get(TipoSlotMissa.SEXTA_ADORACAO)
        if not missa:
            return

        todos = [c for membros in grupos_map.values() for c in membros]
        idx = 0
        for d in datas:
            if d.weekday() != 4:
                continue
            selecionados: list[Coroinha] = []
            for _ in range(quantidade):
                if not todos:
                    break
                selecionados.append(todos[idx % len(todos)])
                idx += 1
            cls._criar_escala_com_membros(
                data=d,
                missa=missa,
                usuario=usuario,
                escala_mensal=escala_mensal,
                coroinhas=selecionados,
                observacao=OBS_SEXTA,
            )

    @classmethod
    def _gerar_quartas(cls, datas, escala_mensal, missas, usuario):
        missa = missas.get(TipoSlotMissa.QUARTA_VOLUNTARIOS)
        if not missa:
            return

        for d in datas:
            if d.weekday() != 2:
                continue
            cls._criar_escala_com_membros(
                data=d,
                missa=missa,
                usuario=usuario,
                escala_mensal=escala_mensal,
                coroinhas=[],
                observacao=OBS_QUARTA,
                voluntarios=True,
            )

    @classmethod
    def _gerar_comunidade(cls, datas, escala_mensal, missas, usuario, quantidade):
        missa = Missa.objects.filter(
            ativa=True,
            tipo_slot=TipoSlotMissa.COMUNIDADE_DOMINGO,
            local=LocalCelebracao.COMUNIDADE,
        ).first()
        if not missa:
            return

        candidatos = list(
            Coroinha.objects.filter(status__in=[StatusCoroinha.ATIVO, StatusCoroinha.EM_FORMACAO]).order_by(
                "nome"
            )
        )
        idx = 0
        for d in datas:
            if d.weekday() != 6:
                continue
            selecionados = []
            for _ in range(quantidade):
                if not candidatos:
                    break
                selecionados.append(candidatos[idx % len(candidatos)])
                idx += quantidade
            cls._criar_escala_com_membros(
                data=d,
                missa=missa,
                usuario=usuario,
                escala_mensal=escala_mensal,
                coroinhas=selecionados,
            )
