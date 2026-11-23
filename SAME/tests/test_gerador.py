import csv
import tempfile
import unittest
from pathlib import Path
from gerar_dados import gerar

class TestGerador(unittest.TestCase):
    def test_consistencia_e_reproducibilidade(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            gerar(a); gerar(b)
            for nome in ('produtos.csv', 'movimentacoes.csv'):
                self.assertEqual((Path(a)/nome).read_bytes(), (Path(b)/nome).read_bytes())
            with (Path(a)/'produtos.csv').open(encoding='utf-8') as f:
                produtos = list(csv.DictReader(f))
            saldos = {p['produto_id']: int(p['estoque_inicial']) for p in produtos}
            self.assertEqual(len(saldos), 150)
            ids = set()
            with (Path(a)/'movimentacoes.csv').open(encoding='utf-8') as f:
                for m in csv.DictReader(f):
                    self.assertNotIn(m['movimentacao_id'], ids)
                    ids.add(m['movimentacao_id'])
                    self.assertIn(m['produto_id'], saldos)
                    self.assertIn(m['tipo'], ('ENTRADA', 'SAIDA'))
                    q = int(m['quantidade'])
                    self.assertGreater(q, 0)
                    saldos[m['produto_id']] += q if m['tipo']=='ENTRADA' else -q
                    self.assertGreaterEqual(saldos[m['produto_id']], 0)
