"""Indicadores gerenciais calculados sobre o resultado validado pelo analisador."""
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path

from analisador import ler_csv


def curva_abc(resultado):
    """ABC por valor de SAÍDAS (unidades saídas x custo unitário), não receita."""
    itens = []
    for p in resultado['produtos'].values():
        consumo = p['custo_unitario'] * p['saidas']
        itens.append({'produto_id': p['produto_id'], 'nome': p['nome'],
                      'categoria': p['categoria'], 'valor_consumo': consumo,
                      'quantidade_saida': p['saidas'], 'saldo': p['saldo']})
    itens.sort(key=lambda x: (-x['valor_consumo'], x['produto_id']))
    total = sum((i['valor_consumo'] for i in itens), Decimal('0'))
    acumulado = Decimal('0')
    for item in itens:
        anterior = acumulado / total * 100 if total else Decimal('0')
        acumulado += item['valor_consumo']
        item['participacao_percentual'] = item['valor_consumo'] / total * 100 if total else Decimal('0')
        item['acumulado_percentual'] = acumulado / total * 100 if total else Decimal('0')
        # Limite usa o acumulado anterior para não deixar classe vazia em concentração extrema
        item['classe'] = 'A' if anterior < 80 else ('B' if anterior < 95 else 'C')
    return itens


def movimentacoes_por_mes(pasta):
    """Agrupa quantidades de entradas e saídas por mês (YYYY-MM)."""
    registros = ler_csv(Path(pasta) / 'movimentacoes.csv',
                        ['movimentacao_id', 'produto_id', 'data', 'tipo', 'quantidade'])
    meses = defaultdict(lambda: {'ENTRADA': 0, 'SAIDA': 0})
    for r in registros:
        mes = date.fromisoformat(r['data']).strftime('%Y-%m')
        meses[mes][r['tipo'].strip().upper()] += int(r['quantidade'])
    return [{'mes': m, 'entradas': v['ENTRADA'], 'saidas': v['SAIDA']}
            for m, v in sorted(meses.items())]


def tabela_produtos(resultado):
    classes = {i['produto_id']: i for i in curva_abc(resultado)}
    tabela = []
    for p in sorted(resultado['produtos'].values(), key=lambda v: v['produto_id']):
        tabela.append({
            'ID': p['produto_id'], 'Produto': p['nome'], 'Categoria': p['categoria'],
            'Saldo': p['saldo'], 'Mínimo': p['estoque_minimo'],
            'Entradas': p['entradas'], 'Saídas': p['saidas'],
            'Valor (R$)': float(p['saldo'] * p['custo_unitario']),
            'Situação': 'Crítico' if p['saldo'] <= p['estoque_minimo'] else 'Normal',
            'Classe ABC': classes[p['produto_id']]['classe'],
            'Última movimentação': p['ultima_movimentacao'].isoformat() if p['ultima_movimentacao'] else '',
        })
    return tabela


def exportar_csv(registros):
    """Gera conteúdo CSV em memória, adequado a botão de download no Streamlit."""
    if not registros:
        return ''
    arquivo = StringIO()
    escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]), delimiter=';')
    escritor.writeheader()
    escritor.writerows(registros)
    return '\ufeff' + arquivo.getvalue()
