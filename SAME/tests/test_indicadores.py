import unittest
from decimal import Decimal
from pathlib import Path
from analisador import analisar, DADOS
from indicadores import curva_abc, movimentacoes_por_mes, tabela_produtos, exportar_csv

class TestIndicadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = analisar(DADOS)

    def test_classes_e_total(self):
        itens = curva_abc(self.r)
        self.assertEqual(len(itens), 150)
        self.assertEqual({i['classe'] for i in itens}, {'A','B','C'})
        self.assertAlmostEqual(float(sum((i['participacao_percentual'] for i in itens), Decimal(0))), 100, places=5)

    def test_movimentos_por_mes(self):
        meses = movimentacoes_por_mes(DADOS)
        self.assertEqual(sum(m['entradas'] for m in meses), self.r['total_entradas'])
        self.assertEqual(sum(m['saidas'] for m in meses), self.r['total_saidas'])

    def test_tabela_alertas(self):
        tabela = tabela_produtos(self.r)
        self.assertEqual(sum(v['Situação']=='Crítico' for v in tabela), len(self.r['criticos']))

    def test_exportacao(self):
        self.assertIn('Classe ABC', exportar_csv(tabela_produtos(self.r)))
        self.assertIn(';', exportar_csv(tabela_produtos(self.r)))

if __name__ == '__main__':
    unittest.main()
