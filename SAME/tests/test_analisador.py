import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from gerar_dados import gerar
from analisador import analisar, ErroDados


class TestAnalisador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        gerar(self.pasta)

    def test_base_gerada(self):
        r = analisar(self.pasta)
        self.assertEqual(len(r['produtos']), 150)
        self.assertEqual(r['movimentacoes'], 3127)
        self.assertGreaterEqual(r['valor_total'], Decimal('0'))
        self.assertTrue(all(p['saldo'] >= 0 for p in r['produtos'].values()))

    def test_produto_duplicado(self):
        arquivo = self.pasta / 'produtos.csv'
        with arquivo.open(encoding='utf-8', newline='') as f:
            linhas = list(csv.reader(f))
        linhas.append(linhas[1])
        with arquivo.open('w', encoding='utf-8', newline='') as f:
            csv.writer(f).writerows(linhas)
        with self.assertRaisesRegex(ErroDados, 'duplicado'):
            analisar(self.pasta)

    def test_produto_inexistente(self):
        arquivo = self.pasta / 'movimentacoes.csv'
        texto = arquivo.read_text(encoding='utf-8')
        arquivo.write_text(texto.replace('P001', 'P999', 1), encoding='utf-8')
        with self.assertRaisesRegex(ErroDados, 'inexistente'):
            analisar(self.pasta)

    def test_saida_sem_saldo(self):
        arquivo = self.pasta / 'movimentacoes.csv'
        with arquivo.open(encoding='utf-8', newline='') as f:
            linhas = list(csv.DictReader(f))
        linhas[0]['tipo'] = 'SAIDA'
        linhas[0]['quantidade'] = '99999'
        with arquivo.open('w', encoding='utf-8', newline='') as f:
            escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
            escritor.writeheader()
            escritor.writerows(linhas)
        with self.assertRaisesRegex(ErroDados, 'saída maior'):
            analisar(self.pasta)


if __name__ == '__main__':
    unittest.main()
