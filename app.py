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

# --- ARQUIVOS E PERSISTÊNCIA ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict) and "tags" in conteudo:
                    return conteudo
                elif isinstance(conteudo, dict):
                    return {"tags": conteudo, "last_selection": {}}
        except: 
            return padrao
    return padrao

def salvar_tags(dados):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    
    .main .block-container { padding-top: 40px !important; max-width: 98% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }

    [data-testid="stDataFrame"] { height: 75vh !important; width: 100% !important; }

    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; transition: all 0.3s ease !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        df = conn.read(ttl="1s").dropna(how='all')
        # Normalização imediata das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "history" not in st.session_state: st.session_state.history = []
if "history_idx" not in st.session_state: st.session_state.history_idx = -1
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES DE SINCRONIZAÇÃO E HISTÓRICO ---
def sync_to_sheets(df):
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
        sheet = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
        
        # Correção do erro 'nan': preencher vazios e converter para string
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

def transformar_curso(chave):
    entrada = st.session_state[chave].strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper()
    else: st.session_state[chave] = entrada.upper()

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave])
    if len(valor) == 11:
        st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        st.write("")
        _, b1, b2, _ = st.columns([1.2, 1.9, 1.9, 0.2])
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({
                        "ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                        "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]),
                        "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), 
                        "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(),
                        "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                    })
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                        d_f = [[ "ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]] for a in st.session_state.lista_previa]
                        ws.append_rows(d_f, value_input_option='RAW')
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1
                        st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    c_undo, c_redo, c_search, c_st, c_un, c_ref = st.columns([0.3, 0.3, 2.0, 1.0, 1.0, 0.3])
    
    if c_undo.button("↩️"):
        if st.session_state.history_idx > 0:
            st.session_state.history_idx -= 1
            st.session_state.df_gerenciamento = st.session_state.history[st.session_state.history_idx].copy()
            sync_to_sheets(st.session_state.df_gerenciamento); st.rerun()
            
    if c_redo.button("↪️"):
        if st.session_state.history_idx < len(st.session_state.history) - 1:
            st.session_state.history_idx += 1
            st.session_state.df_gerenciamento = st.session_state.history[st.session_state.history_idx].copy()
            sync_to_sheets(st.session_state.df_gerenciamento); st.rerun()

    with c_search: bu = st.text_input("Buscar", placeholder="Nome ou ID", label_visibility="collapsed", key="search_ger")
    with c_st: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], label_visibility="collapsed", key="status_ger")
    with c_un: fu = st.selectbox("Unidade", ["Todos", "MGA"], label_visibility="collapsed", key="unid_ger")
    with c_ref: 
        if st.button("🔄", key="ref_ger"): st.cache_data.clear(); st.rerun()

    if "df_gerenciamento" not in st.session_state:
        df_raw = safe_read()
        if not df_raw.empty:
            st.session_state.df_gerenciamento = df_raw
            add_to_history(df_raw)

    if "df_gerenciamento" in st.session_state and not st.session_state.df_gerenciamento.empty:
        df_view = st.session_state.df_gerenciamento.copy()
        if bu: df_view = df_view[df_view['ALUNO'].str.contains(bu, case=False, na=False) | df_view['ID'].astype(str).str.contains(bu, case=False, na=False)]
        if fs != "Todos": df_view = df_view[df_view['STATUS'] == fs]
        if fu != "Todos": df_view = df_view[df_view['UNID.'] == fu]

        st.session_state.df_gerenciamento = st.data_editor(
            df_view,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "STATUS": st.column_config.SelectboxColumn("STATUS", options=["ATIVO", "CANCELADO"], required=True),
                "ID": st.column_config.TextColumn("ID", disabled=True),
            },
            key="editor_geral",
            on_change=handle_editor_change
        )

# --- ABA 3: RELATÓRIOS (CORREÇÃO DT_MAT) ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        dt_col = "DT_MAT" # Nome correto da coluna na planilha 
        if dt_col in df_r.columns:
            df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            iv = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
                col_pagto = "PAGTO" if "PAGTO" in df_r.columns else "PAGAMENTO"
                col_curso = "CURSO"; col_vend = "VENDEDOR"; col_cid = "CIDADE"

                df_f['v_rec'] = df_f[col_pagto].apply(extrair_valor_recebido)
                df_f['v_tic'] = df_f[col_pagto].apply(extrair_valor_geral)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">TOTAL RECEBIDO</span><h2 style="font-size:22px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c5:
                    tm_b = df_f[df_f[col_pagto].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
                    tm_c = df_f[df_f[col_pagto].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
                    st.markdown(f'<div class="card-hud neon-purple"><span class="stat-label">TICKET MÉDIO</span><div style="font-size:18px; font-weight:bold; color:#e0e0e0;">BOL: R${tm_b:.0f}<br>CAR: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
                with c6:
                    c_banc = len(df_f[df_f[col_curso].str.contains("BANCÁRIO", case=False, na=False)])
                    c_agro = len(df_f[df_f[col_curso].str.contains("AGRO", case=False, na=False)])
                    c_ing = len(df_f[df_f[col_curso].str.contains("INGLÊS", case=False, na=False)])
                    c_tec = len(df_f[df_f[col_curso].str.contains("TECNOLOGIA|INFORMÁTICA", case=False, na=False)])
                    st.markdown(f'''<div class="card-hud neon-blue"><span class="stat-label">POR ÁREA</span><div style="font-size:15px; text-align:left; color:#e0e0e0; line-height:1.4; padding-left:5px;">BANC: <b style="color:#00f2ff;">{c_banc}</b> | AGRO: <b style="color:#00f2ff;">{c_agro}</b><br>INGL: <b style="color:#00f2ff;">{c_ing}</b> | TECN: <b style="color:#00f2ff;">{c_tec}</b></div></div>''', unsafe_allow_html=True)

                st.write(""); col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("<h4 style='text-align:center; color:#00f2ff;'>📍 CIDADES E VENDEDORES</h4>", unsafe_allow_html=True)
                    df_city_full = df_f.copy(); df_city_full["V_L"] = df_city_full[col_vend].str.split(" - ").str[0].str.strip()
                    top_c = df_city_full[col_cid].value_counts().head(5).index
                    city_data = [{"Cidade": c, "Qtd": len(df_city_full[df_city_full[col_cid] == c]), "Vendedores": ", ".join(list(df_city_full[df_city_full[col_cid] == c]["V_L"].unique()))} for c in top_c]
                    df_p = pd.DataFrame(city_data)
                    fig = go.Figure(go.Bar(x=df_p['Cidade'], y=df_p['Qtd'], text=df_p.apply(lambda r: f"<b>{r['Qtd']}</b><br><span style='font-size:11px; color:#ff007a;'>{r['Vendedores']}</span>", axis=1), textposition='outside', marker=dict(color='#00f2ff')))
                    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450); st.plotly_chart(fig, use_container_width=True)
        else: st.error("Coluna 'DT_MAT' não encontrada.")

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    # Lógica de processamento mantida integralmente...
