"""Validação e análise básica de estoque em CSV (biblioteca padrão)."""
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

DADOS = Path(__file__).resolve().parent / 'dados'


class ErroDados(ValueError):
    """Erro de estrutura ou consistência nos arquivos importados."""


def ler_csv(caminho, campos):
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ErroDados(f'Arquivo não encontrado: {caminho}')
    with caminho.open('r', encoding='utf-8-sig', newline='') as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames or not set(campos).issubset(leitor.fieldnames):
            raise ErroDados(f'{caminho.name}: colunas necessárias: {", ".join(campos)}')
        return list(leitor)


def inteiro(valor, descricao, minimo=0):
    try:
        numero = int(valor)
        if str(numero) != str(valor).strip() or numero < minimo:
            raise ValueError
        return numero
    except (ValueError, TypeError):
        raise ErroDados(f'{descricao}: esperado inteiro >= {minimo}; recebido {valor!r}') from None


def analisar(pasta=DADOS, referencia=date(2026, 11, 20)):
    """Analisa produtos/movimentações, rejeita dados inválidos e devolve indicadores."""
    pasta = Path(pasta)
    produtos_csv = ler_csv(pasta / 'produtos.csv',
        ['produto_id', 'nome', 'categoria', 'custo_unitario', 'estoque_inicial', 'estoque_minimo'])
    movimentos_csv = ler_csv(pasta / 'movimentacoes.csv',
        ['movimentacao_id', 'produto_id', 'data', 'tipo', 'quantidade'])
    if not produtos_csv:
        raise ErroDados('A lista de produtos está vazia')

    produtos = {}
    for linha, item in enumerate(produtos_csv, 2):
        codigo = (item['produto_id'] or '').strip()
        if not codigo or codigo in produtos:
            raise ErroDados(f'produtos.csv linha {linha}: ID vazio ou duplicado: {codigo}')
        if not (item['nome'] or '').strip() or not (item['categoria'] or '').strip():
            raise ErroDados(f'produtos.csv linha {linha}: nome/categoria obrigatórios')
        try:
            custo = Decimal(item['custo_unitario'])
            if not custo.is_finite() or custo < 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError):
            raise ErroDados(f'produtos.csv linha {linha}: custo inválido') from None
        inicial = inteiro(item['estoque_inicial'], f'produtos.csv linha {linha}: estoque inicial')
        minimo = inteiro(item['estoque_minimo'], f'produtos.csv linha {linha}: estoque mínimo')
        produtos[codigo] = {
            'produto_id': codigo, 'nome': item['nome'].strip(),
            'categoria': item['categoria'].strip(), 'custo_unitario': custo,
            'estoque_minimo': minimo, 'saldo': inicial, 'ultima_movimentacao': None,
            'entradas': 0, 'saidas': 0,
        }

    ids = set()
    movimentos = []
    for linha, item in enumerate(movimentos_csv, 2):
        mid = (item['movimentacao_id'] or '').strip()
        codigo = (item['produto_id'] or '').strip()
        if not mid or mid in ids:
            raise ErroDados(f'movimentacoes.csv linha {linha}: ID vazio ou duplicado')
        ids.add(mid)
        if codigo not in produtos:
            raise ErroDados(f'movimentacoes.csv linha {linha}: produto inexistente {codigo}')
        try:
            dia = date.fromisoformat(item['data'])
        except (ValueError, TypeError):
            raise ErroDados(f'movimentacoes.csv linha {linha}: data inválida') from None
        if dia > referencia:
            raise ErroDados(f'movimentacoes.csv linha {linha}: movimentação após a data de referência')
        tipo = (item['tipo'] or '').strip().upper()
        if tipo not in ('ENTRADA', 'SAIDA'):
            raise ErroDados(f'movimentacoes.csv linha {linha}: tipo inválido')
        quantidade = inteiro(item['quantidade'], f'movimentacoes.csv linha {linha}: quantidade', 1)
        movimentos.append((dia, linha, codigo, tipo, quantidade))

    # Ordenação cronológica evita que a ordem das linhas altere o saldo histórico.
    for dia, linha, codigo, tipo, quantidade in sorted(movimentos):
        p = produtos[codigo]
        if tipo == 'ENTRADA':
            p['saldo'] += quantidade
            p['entradas'] += quantidade
        else:
            if p['saldo'] < quantidade:
                raise ErroDados(f'movimentacoes.csv linha {linha}: saída maior que o saldo disponível')
            p['saldo'] -= quantidade
            p['saidas'] += quantidade
        p['ultima_movimentacao'] = dia

    criticos = [p for p in produtos.values() if p['saldo'] <= p['estoque_minimo']]
    inativos = [p for p in produtos.values() if p['ultima_movimentacao'] is None
                or (referencia - p['ultima_movimentacao']).days > 30]
    valor = sum((p['saldo'] * p['custo_unitario'] for p in produtos.values()), Decimal('0'))
    return {'produtos': produtos, 'movimentacoes': len(movimentos),
            'criticos': criticos, 'inativos': inativos, 'valor_total': valor,
            'total_entradas': sum(p['entradas'] for p in produtos.values()),
            'total_saidas': sum(p['saidas'] for p in produtos.values())}


def executar():
    resultado = analisar()
    print('=== SAME | RESUMO DE ESTOQUE ===')
    print('Produtos:', len(resultado['produtos']))
    print('Movimentações:', resultado['movimentacoes'])
    print('Entradas (unidades):', resultado['total_entradas'])
    print('Saídas (unidades):', resultado['total_saidas'])
    print('Valor em estoque: R$ {:.2f}'.format(resultado['valor_total']))
    print('Produtos críticos:', len(resultado['criticos']))
    print('Produtos sem movimentação há mais de 30 dias:', len(resultado['inativos']))
    print('\nPrimeiros 5 produtos críticos:')
    for p in sorted(resultado['criticos'], key=lambda p: p['produto_id'])[:5]:
        print(f"  {p['produto_id']}: saldo {p['saldo']} / mínimo {p['estoque_minimo']}")


if __name__ == '__main__':
    try:
        executar()
    except ErroDados as erro:
        raise SystemExit(f'ERRO NOS DADOS: {erro}')
