# SAME — Sistema de Análise e Monitoramento de Estoque

Projeto Integrador de Laboratório de Programação, desenvolvido em Python. Dados **sintéticos**, sem vínculo com operação empresarial real.

## Requisitos
- Windows com Python 3.10+ (recomendado Python 3.13)
- VS Code opcional

## Instalação no PowerShell

Primeiramente, instale o Python 3.13 (caso ainda não esteja instalado):

```powershell
winget install --id Python.Python.3.13 -e --source winget
```

Após a instalação, reinicie o terminal. Com o Git instalado, execute:

```powershell
git clone https://github.com/nicolas-oliveiradev/SAME-Projeto-Integrador.git
cd SAME-Projeto-Integrador
cd SAME
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se `python` não for reconhecido, experimente `py -3.13 -m venv .venv`.

## Executar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Acesse http://localhost:8501 no navegador.

## Módulos
- `gerar_dados.py`: gera 150 produtos e 3127 movimentações sintéticas com semente 42
- `analisador.py`: valida CSV, calcula saldo histórico, entradas, saídas, valores e alertas
- `indicadores.py`: classes ABC por custo das saídas, agregações mensais e exportação CSV
- `app.py`: interface Streamlit com filtros, indicadores, gráficos e importação de arquivos

## Arquivos CSV
`produtos.csv`: `produto_id,nome,categoria,custo_unitario,estoque_inicial,estoque_minimo`

`movimentacoes.csv`: `movimentacao_id,produto_id,data,tipo,quantidade`

Datas no padrão AAAA-MM-DD; tipo ENTRADA ou SAIDA; quantidades inteiras positivas; custo decimal com ponto. Arquivos importados devem ter nomes e estrutura compatíveis com os dois CSV de demonstração.

## Regras e limitações
- Saldo = estoque inicial + entradas - saídas; cada saída deve caber no saldo da data.
- Crítico: saldo <= estoque mínimo. Inativo: sem movimentação há mais de 30 dias da referência.
- ABC: custo unitário * unidades de saída; 80/95% do **valor de consumo**; não mede faturamento, lucro nem previsão de demanda.
- A data de referência é um **corte de validação**, não recalcula o saldo retroativamente: arquivos com datas posteriores são rejeitados.
- Não inclui autenticação, banco de dados, múltiplos depósitos nem integração de sistemas.
- Ao subir CSV próprios, os arquivos são processados em diretório temporário e não substituem os dados de exemplo.

