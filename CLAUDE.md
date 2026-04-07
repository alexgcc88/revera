# Revera — Project Summary (handoff)
*Siemens Advanta · NOVA Business Case 2026*

## O que é

Revera é um AI agent com interface Streamlit para explorar forecasts hierárquicos de Revenue da Siemens Advanta. Usa Groq API (Llama 3.3 70B, gratuito) como NLU, MinT shrink para reconciliação hierárquica, e XGBoost para as previsões P.43–48.

---

## Estado actual (sessão anterior)

### Pipeline de modelação (Jupyter notebooks)
- CRISP-DM completo: data prep, EDA (pendente), modelling, avaliação
- Target: Delta (Revenue(t) − Revenue(t−1)) para tree models
- Modelos: LightGBM, XGBoost, Random Forest, Gradient Boosting, ETS
- Reconciliação: MinT shrink via `hierarchicalforecast` (Nixtla)
- R²: BU=0.969, Segment=0.986, Subsegment=0.972
- Forecasts P.43–48 gerados com XGBoost → ficheiro `submission_xgboost_mint_periods_43_48.csv`
- Optuna tuning: **ainda por fazer** (era o próximo passo no pipeline)

### Revera (AI Agent)
Ficheiros na pasta do projecto:

| Ficheiro | Descrição |
|---|---|
| `app.py` | Interface Streamlit com chat, breadcrumb, follow-ups, Export PDF |
| `builders.py` | Lógica de todos os intents → charts + tabelas Plotly/pandas |
| `data.py` | Dados completos: histórico P.1–42 + forecast P.43–48 (gerado dos parquets reais) |
| `nlu.py` | Chama Groq API, devolve JSON com intent/level/ids/sort/periods |
| `pdf_export.py` | Relatório PDF com matplotlib + reportlab (2 páginas, 177KB) |
| `requirements.txt` | Todas as dependências |
| `.streamlit/secrets.toml` | Groq API key (não vai para git) |
| `.gitignore` | Exclui secrets, parquets, csvs |
| `test_builders.py` | 52 testes básicos (todos a passar) |
| `test_builders_hard.py` | 48 testes de edge cases (todos a passar) |
| `revera_icon.png` | Ícone hexagonal teal/dark |

### Arquitectura do Revera

```
User query
    → nlu.py (Groq/Llama) → JSON {intent, level, ids, sort, periods}
    → builders.py → {text, charts, tables, cards, followups, export_pdf}
    → app.py renders everything
```

**Intents suportados:** `executive`, `metrics`, `overview`, `ranking`, `drilldown`, `compare`, `period_diff`, `trend`, `anomaly`, `error`

**Dados em `data.py`:**
- `BU_HIST`, `SEG_HIST`, `SUB_HIST` — histórico P.1–42 (4 BUs, 24 segs, 134 subs)
- `BU_FC`, `SEG_FC`, `SUB_FC` — forecast P.43–48 (XGBoost + MinT)
- `BU`, `SEG`, `SUB` — aliases para P.37–42 (legacy compat com builders)
- `PERIODS_HIST = [1..42]`, `PERIODS_FORECAST = [43..48]`
- `SUB_TO_SEG`, `SEG_TO_BU` — mapeamentos hierárquicos

**SQLite in-memory (builders.py):**
- Tabela `forecast` — P.37–42 (legacy, usada pelos intents normais)
- Tabela `hist` — P.1–42 completo
- Tabela `forecast48` — P.43–48

### Features do Revera
- Chat em linguagem natural
- Breadcrumb de contexto (Context › BU: SSI037 › Segment: SSI03781)
- Follow-up chips dinâmicos após cada resposta
- Gráfico histórico+forecast azul/laranja (igual ao XGBoost plot)
- CAGR em vez de growth simples
- Volatilidade (CV%) nas tabelas
- Intent `trend` — regressão linear + classificação Growing/Declining/Flat
- Intent `anomaly` — IQR sobre deltas period-over-period
- Export CSV
- Export PDF (executive summary → 2 páginas com gráficos e tabelas)
- API key lida de `st.secrets` automaticamente (para deploy)

---

## O que falta fazer


3. **Deploy Streamlit Cloud** — push para GitHub + configurar secrets

### Médio prazo
4. **Actualizar sidebar** — mostrar "Periods: 37–48" e "Forecast: P.43–48 (XGBoost)"
5. **NLU para períodos de forecast** — actualmente os períodos válidos no NLU são só 37–42; devia incluir 43–48 para queries como "show revenue in P.45"
6. **Intent `forecast`** — query dedicada para ver os forecasts P.43–48 sem ser só pelo executive

### Bugs conhecidos
- Nenhum de momento (100/100 testes a passar)

---

## Como correr localmente

```bash
pip install -r requirements.txt
# Cria .streamlit/secrets.toml com GROQ_API_KEY = "gsk_..."
streamlit run app.py
```

## Testes

```bash
python test_builders.py          # 52 testes básicos
python test_builders_hard.py     # 48 edge cases
python test_builders.py && python test_builders_hard.py  # ambos
```

## Deploy Streamlit Cloud

1. Push da pasta para GitHub (`.streamlit/secrets.toml` está no `.gitignore`)
2. `share.streamlit.io` → New app → selecciona repo e `app.py`
3. Settings → Secrets → cola `GROQ_API_KEY = "gsk_..."`
4. Deploy

---

## Stack técnico

- **Frontend:** Streamlit 1.32+
- **NLU:** Groq API — Llama 3.3 70B Versatile (gratuito, sem cartão)
- **Charts:** Plotly (app) + Matplotlib (PDF)
- **PDF:** ReportLab + Matplotlib
- **Data:** SQLite in-memory + pandas
- **Modelação:** XGBoost, LightGBM, RF, GBM, ETS + MinT shrink (Nixtla)
- **Testes:** pytest-style manual (test_builders.py + test_builders_hard.py)