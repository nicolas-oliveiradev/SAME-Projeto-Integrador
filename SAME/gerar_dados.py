"""Gera uma base sintética de estoque, com resultados reproduzíveis."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

PASTA = Path(__file__).resolve().parent / 'dados'
INICIO = date(2026, 6, 1)
FIM = date(2026, 11, 20)


def gerar(pasta=PASTA, semente=42):
    rng = random.Random(semente)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    categorias = ['Fixadores', 'Ferramentas', 'Componentes', 'EPIs', 'Consumíveis']
    produtos = []
    saldos = {}
    for i in range(1, 151):
        codigo = f'P{i:03d}'
        categoria = categorias[(i-1) % len(categorias)]
        inicial = rng.randint(30, 200)
        produtos.append(dict(produto_id=codigo, nome=f'{categoria} {i:03d}', categoria=categoria,
            custo_unitario=f'{rng.uniform(2, 250):.2f}', estoque_inicial=inicial, estoque_minimo=rng.randint(10, 40)))
        saldos[codigo] = inicial
    movimentos = []
    for dia in range((FIM-INICIO).days+1):
        data = INICIO + timedelta(days=dia)
        for _ in range(rng.randint(12, 24)):
            # Os últimos oito produtos ficam sem movimentação nos últimos 30 dias.
            produto = rng.choice(produtos[:-8] if data > FIM-timedelta(days=30) else produtos)
            codigo = produto['produto_id']
            tipo = rng.choice(['ENTRADA', 'SAIDA', 'SAIDA']) if saldos[codigo] else 'ENTRADA'
            quantidade = rng.randint(1, 30) if tipo == 'ENTRADA' else rng.randint(1, min(25, saldos[codigo]))
            saldos[codigo] += quantidade if tipo == 'ENTRADA' else -quantidade
            movimentos.append(dict(movimentacao_id=f'M{len(movimentos)+1:05d}', produto_id=codigo,
                data=data.isoformat(), tipo=tipo, quantidade=quantidade))
    for nome, registros in [('produtos.csv', produtos), ('movimentacoes.csv', movimentos)]:
        with (pasta/nome).open('w', encoding='utf-8', newline='') as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]))
            escritor.writeheader()
            escritor.writerows(registros)
    return len(produtos), len(movimentos)


if __name__ == '__main__':
    p, m = gerar()
    print(f'{p} produtos e {m} movimentações gerados em {PASTA}')
