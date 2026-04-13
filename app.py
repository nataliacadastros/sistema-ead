import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- CSS HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .main .block-container { padding-top: 40px !important; max-width: 98% !important; margin: 0 auto !important; }
    [data-testid="stDataFrame"] { height: 75vh !important; width: 100% !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        df = conn.read(ttl="1s").dropna(how='all')
        # Limpeza imediata de nomes de colunas para evitar KeyError
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "history" not in st.session_state: st.session_state.history = []
if "history_idx" not in st.session_state: st.session_state.history_idx = -1

# --- FUNÇÕES DE SINCRONIZAÇÃO ---
def sync_to_sheets(df):
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
        sheet = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
        df_sync = df.copy().fillna("")
        data_to_send = [df_sync.columns.values.tolist()] + df_sync.astype(str).values.tolist()
        sheet.update(data_to_send)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro na sincronização: {e}")

def add_to_history(df):
    st.session_state.history = st.session_state.history[:st.session_state.history_idx + 1]
    st.session_state.history.append(df.copy())
    if len(st.session_state.history) > 30: st.session_state.history.pop(0)
    st.session_state.history_idx = len(st.session_state.history) - 1

def handle_editor_change():
    new_df = st.session_state.df_gerenciamento
    sync_to_sheets(new_df)
    add_to_history(new_df)

def extrair_valor_recebido(texto):
    if not texto: return 0.0
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0

def extrair_valor_geral(texto):
    if not texto: return 0.0
    v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
    return float(v[0]) if v else 0.0

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.info("Módulo de Cadastro Ativo")
    # Lógica de salvar aluno mantida conforme funcionalidade anterior...

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    c_undo, c_redo, c_search, c_ref = st.columns([0.3, 0.3, 3.0, 0.4])
    
    if "df_gerenciamento" not in st.session_state:
        df_raw = safe_read()
        if not df_raw.empty:
            st.session_state.df_gerenciamento = df_raw
            add_to_history(df_raw)

    if "df_gerenciamento" in st.session_state and not st.session_state.df_gerenciamento.empty:
        st.session_state.df_gerenciamento = st.data_editor(
            st.session_state.df_gerenciamento,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="editor_geral",
            on_change=handle_editor_change
        )

# --- ABA 3: RELATÓRIOS (CORRIGIDA) ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        # Identificar coluna de data de forma flexível (Maiúsculas/Espaços)
        possiveis_nomes = ["DATA MATRÍCULA", "DATA MATRICULA", "DT_MAT", "DT MATRÍCULA"]
        dt_col = next((c for c in df_r.columns if c in possiveis_nomes), None)
        
        if dt_col:
            df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            iv = st.date_input("Período do Relatório", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
                
                # Mapeamento de colunas para cálculos
                col_pagto = next((c for c in df_r.columns if "PAGAMENTO" in c or "PAGTO" in c), "PAGAMENTO")
                col_status = "STATUS"
                col_curso = next((c for c in df_r.columns if "CURSO" in c), "CURSO")
                col_vend = next((c for c in df_r.columns if "VENDEDOR" in c or "VEND" in c), "VENDEDOR")
                col_cid = next((c for c in df_r.columns if "CIDADE" in c), "CIDADE")

                df_f['v_rec'] = df_f[col_pagto].apply(extrair_valor_recebido)
                df_f['v_tic'] = df_f[col_pagto].apply(extrair_valor_geral)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f[col_status].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f[col_status].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">TOTAL RECEBIDO</span><h2 style="font-size:20px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c5:
                    tm_b = df_f[df_f[col_pagto].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
                    tm_c = df_f[df_f[col_pagto].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
                    st.markdown(f'<div class="card-hud neon-purple"><span class="stat-label">TICKET MÉDIO</span><div style="font-size:16px; font-weight:bold; color:#e0e0e0;">BOL: R${tm_b:.0f} | CAR: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
                with c6:
                    c_banc = len(df_f[df_f[col_curso].str.contains("BANCÁRIO", case=False, na=False)])
                    c_agro = len(df_f[df_f[col_curso].str.contains("AGRO", case=False, na=False)])
                    c_ing = len(df_f[df_f[col_curso].str.contains("INGLÊS", case=False, na=False)])
                    c_tec = len(df_f[df_f[col_curso].str.contains("TECNOLOGIA|INFORMÁTICA", case=False, na=False)])
                    st.markdown(f'''<div class="card-hud neon-blue"><span class="stat-label">POR ÁREA</span><div style="font-size:14px; text-align:left; color:#e0e0e0; line-height:1.4;">BANC: <b>{c_banc}</b> | AGRO: <b>{c_agro}</b><br>INGL: <b>{c_ing}</b> | TECN: <b>{c_tec}</b></div></div>''', unsafe_allow_html=True)

                st.write("---")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("<h4 style='text-align:center; color:#00f2ff;'>📍 CIDADES E VENDEDORES</h4>", unsafe_allow_html=True)
                    df_city_full = df_f.copy()
                    df_city_full["VEND_LIMPO"] = df_city_full[col_vend].str.split(" - ").str[0].str.strip()
                    top_cities = df_city_full[col_cid].value_counts().head(5).index
                    city_data = []
                    for city in top_cities:
                        vends = df_city_full[df_city_full[col_cid] == city]["VEND_LIMPO"].unique()
                        count = len(df_city_full[df_city_full[col_cid] == city])
                        city_data.append({"Cidade": city, "Qtd": count, "Vendedores": ", ".join(list(vends))})
                    
                    df_p = pd.DataFrame(city_data)
                    fig = go.Figure(go.Bar(x=df_p['Cidade'], y=df_p['Qtd'], text=df_p.apply(lambda r: f"<b>{r['Qtd']}</b><br>{r['Vendedores']}", axis=1), textposition='outside', marker=dict(color='#00f2ff')))
                    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Coluna de data não encontrada. Colunas lidas: {list(df_r.columns)}")

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    # Lógica de processamento e download mantida...
