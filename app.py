import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- DEFINIÇÃO DO CAMINHO DA LOGO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

# --- CONFIGURAÇÕES DA PÁGINA ---
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
    [data-testid="stAppViewBlockContainer"] { padding-top: 40px !important; padding-left: 10px !important; padding-right: 10px !important; max-width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #121629; border-bottom: 1px solid #1f295a; position: fixed; top: 0; left: 0 !important; width: 100vw !important; z-index: 999; justify-content: center; height: 35px !important; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 15px !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    
    /* AgGrid Neon Style */
    .ag-theme-balham-dark {
        --ag-header-background-color: #121629;
        --ag-header-foreground-color: #00f2ff;
        --ag-background-color: #0b0e1e;
        --ag-odd-row-background-color: #0d111f;
        --ag-row-hover-color: rgba(0, 242, 255, 0.1);
        --ag-selected-row-background-color: rgba(0, 242, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
def safe_read():
    try: return conn.read(ttl="0").dropna(how='all')
    except: return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES AUXILIARES ---
def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None

def extrair_valor_geral(texto):
    if not texto: return 0.0
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

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
    if len(valor) == 11: st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    s_ge = f"g_{st.session_state.reset_geral}"
    c_id, c_nom = st.columns([1, 4])
    c_id.text_input("ID:", key=f"f_id_{s_al}")
    c_nom.text_input("ALUNO:", key=f"f_nome_{s_al}")
    c_t1, c_t2, c_cpf = st.columns(3)
    c_t1.text_input("TEL. RESPONSÁVEL:", key=f"f_tel_resp_{s_al}")
    c_t2.text_input("TEL. ALUNO:", key=f"f_tel_aluno_{s_al}")
    c_cpf.text_input("CPF RESPONSÁVEL:", key=f"f_cpf_{s_al}", on_change=formatar_cpf, args=(f"f_cpf_{s_al}",))
    c_cid, c_ven = st.columns(2)
    c_cid.text_input("CIDADE:", key=f"f_cid_{s_ge}")
    c_ven.text_input("VENDEDOR:", key=f"f_vend_{s_ge}")
    st.text_input("CURSO:", key=f"in_cur_{s_al}", on_change=transformar_curso, args=(f"in_cur_{s_al}",))
    st.text_area("PAGAMENTO:", key=f"f_pagto_{s_al}")
    st.text_input("DATA:", key=f"f_data_{s_ge}", value=date.today().strftime("%d/%m/%Y"))
    if st.button("💾 SALVAR ALUNO"):
        st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"in_cur_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
        st.session_state.reset_aluno += 1
        st.rerun()
    if st.session_state.lista_previa:
        st.dataframe(pd.DataFrame(st.session_state.lista_previa))
        if st.button("📤 ENVIAR PARA SHEETS"):
            creds_info = st.secrets["connections"]["gsheets"]
            client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
            ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
            rows = [[ "ATIVO", "MGA", "A DEFINIR", "SIM", "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]] for a in st.session_state.lista_previa]
            ws.append_rows(rows); st.session_state.lista_previa = []; st.success("Sucesso!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: GERENCIAMENTO (MOTOR AGGRID) ---
with tab_ger:
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_display = df_g.iloc[::-1].copy()
        
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_selection('single', use_checkbox=False)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(resizable=True, filter=True, sortable=True)
        gb.configure_column("ALUNO", pinned='left', width=250)
        grid_options = gb.build()

        col_t, col_e = st.columns([0.7, 0.3])
        with col_t:
            res = AgGrid(df_display, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED, theme='balham', height=600)
        with col_e:
            sel = res['selected_rows']
            if sel:
                aluno = sel[0] if isinstance(sel, list) else sel.iloc[0]
                st.markdown(f"### 📝 Editar: {aluno['ALUNO']}")
                with st.form("edit_f"):
                    n_st = st.selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if aluno['STATUS']=="ATIVO" else 1)
                    n_tu = st.text_input("TURMA", value=aluno['TURMA'])
                    n_pg = st.text_area("PAGAMENTO", value=aluno['PAGTO'], height=200)
                    if st.form_submit_button("💾 SALVAR"):
                        creds_info = st.secrets["connections"]["gsheets"]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        sh = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                        ids = sh.col_values(7)
                        idx = ids.index(str(aluno['ID'])) + 1
                        sh.update_cell(idx, 1, n_st)
                        sh.update_cell(idx, 3, n_tu.upper())
                        sh.update_cell(idx, 14, n_pg.upper())
                        st.success("Salvo!"); st.cache_data.clear(); st.rerun()
            else: st.info("Selecione um aluno na tabela.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        df_r["Data Matrícula"] = pd.to_datetime(df_r["Data Matrícula"], dayfirst=True, errors='coerce')
        iv = st.date_input("Período", value=(date.today()-timedelta(days=7), date.today()))
        if len(iv)==2:
            df_f = df_r.loc[(df_r["Data Matrícula"].dt.date >= iv[0]) & (df_r["Data Matrícula"].dt.date <= iv[1])]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("MATRÍCULAS", len(df_f))
            c2.metric("ATIVOS", len(df_f[df_f["STATUS"]=="ATIVO"]))
            c3.metric("CANCELADOS", len(df_f[df_f["STATUS"]=="CANCELADO"]))
            st.plotly_chart(go.Figure(go.Bar(x=["Ativos", "Cancelados"], y=[len(df_f[df_f["STATUS"]=="ATIVO"]), len(df_f[df_f["STATUS"]=="CANCELADO"])], marker_color=['#2ecc71', '#ff4b4b'])).update_layout(template="plotly_dark"), use_container_width=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    if modo == "MANUAL":
        c1, c2 = st.columns(2)
        u_id = c1.text_area("IDs"); u_nm = c2.text_area("Nomes")
        u_cr = c1.text_area("Cursos"); u_py = c2.text_area("Pagamentos")
        # Lógica de processamento de tags aqui...
