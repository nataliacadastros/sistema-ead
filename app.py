import streamlit as st
import pandas as pd
import re
import json
import os
import gspread
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed"
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
                return conteudo if isinstance(conteudo, dict) else padrao
        except: return padrao
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

# --- CSS HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    [data-testid="stAppViewBlockContainer"] { padding: 40px 10px !important; max-width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 15px !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    
    /* AgGrid Custom Theme */
    .ag-theme-balham-dark {
        --ag-header-background-color: #121629;
        --ag-header-foreground-color: #00f2ff;
        --ag-odd-row-background-color: #0b0e1e;
        --ag-row-hover-color: rgba(0, 242, 255, 0.1);
        --ag-selected-row-background-color: rgba(0, 242, 255, 0.2);
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        return conn.read(ttl="0").dropna(how='all')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES AUXILIARES ---
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
    if len(valor) == 11:
        st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        s_ge = f"g_{st.session_state.reset_geral}"
        
        col_id, col_nome = st.columns([1, 4])
        col_id.text_input("ID:", key=f"f_id_{s_al}")
        col_nome.text_input("ALUNO:", key=f"f_nome_{s_al}")
        
        col_t1, col_t2, col_cpf = st.columns(3)
        col_t1.text_input("TEL. RESPONSÁVEL:", key=f"f_tel_resp_{s_al}")
        col_t2.text_input("TEL. ALUNO:", key=f"f_tel_aluno_{s_al}")
        col_cpf.text_input("CPF RESPONSÁVEL:", key=f"f_cpf_{s_al}", on_change=formatar_cpf, args=(f"f_cpf_{s_al}",))
        
        col_cid, col_venda = st.columns(2)
        col_cid.text_input("CIDADE:", key=f"f_cid_{s_ge}")
        col_venda.text_input("VENDEDOR:", key=f"f_vend_{s_ge}")
        
        st.text_input("CURSO CONTRATADO:", key=f"in_cur_{s_al}", on_change=transformar_curso, args=(f"in_cur_{s_al}",))
        st.text_area("FORMA DE PAGAMENTO:", key=f"f_pagto_{s_al}")
        st.text_input("DATA MATRÍCULA:", key=f"f_data_{s_ge}", value=date.today().strftime("%d/%m/%Y"))

        if st.button("💾 SALVAR E ADICIONAR À LISTA", use_container_width=True):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({
                    "ID": st.session_state[f"f_id_{s_al}"].upper(),
                    "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                    "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"],
                    "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"],
                    "CPF": st.session_state[f"f_cpf_{s_al}"],
                    "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(),
                    "Course": st.session_state[f"in_cur_{s_al}"].upper(),
                    "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(),
                    "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(),
                    "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                })
                st.session_state.reset_aluno += 1
                st.rerun()

        if st.session_state.lista_previa:
            st.write("---")
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True)
            if st.button("📤 ENVIAR TUDO PARA GOOGLE SHEETS"):
                try:
                    creds_info = st.secrets["connections"]["gsheets"]
                    client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                    rows_to_add = []
                    for a in st.session_state.lista_previa:
                        rows_to_add.append(["ATIVO", "MGA", "A DEFINIR", "SIM", "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                    ws.append_rows(rows_to_add)
                    st.session_state.lista_previa = []
                    st.success("Enviado com sucesso!")
                except Exception as e: st.error(f"Erro: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: GERENCIAMENTO (EDIÇÃO POR CLIQUE) ---
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
        gb.configure_column("STATUS", width=100)
        grid_options = gb.build()

        col_main, col_edit = st.columns([0.7, 0.3])
        
        with col_main:
            grid_response = AgGrid(df_display, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED, theme='balham', height=600)
        
        with col_edit:
            selecao = grid_response['selected_rows']
            if selecao:
                aluno = selecao[0] if isinstance(selecao, list) else selecao.iloc[0]
                st.markdown(f"### 📝 Editar: {aluno['ALUNO']}")
                with st.form("edit_form"):
                    new_status = st.selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if aluno['STATUS'] == "ATIVO" else 1)
                    new_pagto = st.text_area("PAGAMENTO", value=aluno['PAGTO'], height=200)
                    if st.form_submit_button("💾 SALVAR"):
                        try:
                            creds_info = st.secrets["connections"]["gsheets"]
                            client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                            sheet = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                            ids = sheet.col_values(7)
                            row_idx = ids.index(str(aluno['ID'])) + 1
                            sheet.update_cell(row_idx, 1, new_status)
                            sheet.update_cell(row_idx, 14, new_pagto.upper())
                            st.success("Atualizado!")
                            st.cache_data.clear()
                            st.rerun()
                        except: st.error("Erro ao salvar.")
            else: st.info("Clique em um aluno para editar.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        df_r["Data Matrícula"] = pd.to_datetime(df_r["Data Matrícula"], dayfirst=True, errors='coerce')
        iv = st.date_input("Período", value=(date.today()-timedelta(days=7), date.today()))
        if len(iv) == 2:
            df_f = df_r.loc[(df_r["Data Matrícula"].dt.date >= iv[0]) & (df_r["Data Matrícula"].dt.date <= iv[1])]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("MATRÍCULAS", len(df_f))
            c2.metric("ATIVOS", len(df_f[df_f["STATUS"]=="ATIVO"]))
            c3.metric("CANCELADOS", len(df_f[df_f["STATUS"]=="CANCELADO"]))
            
            # Gráfico Simples
            fig = go.Figure(go.Bar(x=["Ativos", "Cancelados"], y=[len(df_f[df_f["STATUS"]=="ATIVO"]), len(df_f[df_f["STATUS"]=="CANCELADO"])], marker_color=['#2ecc71', '#ff4b4b']))
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    if modo == "MANUAL":
        c1, c2 = st.columns(2)
        u_user = c1.text_area("IDs"); u_nome = c2.text_area("Nomes")
        u_cour = c1.text_area("Cursos"); u_pay = c2.text_area("Pagamentos")
    
    with st.expander("🛠️ TAGS DE CURSOS"):
        # Interface simplificada de tags para o código completo
        cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'INGLÊS']
        selected_tags = {}
        for curso in cursos_tags:
            tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, [])
            selected_tags[curso] = st.selectbox(f"Tag para {curso}", [""] + tags_lista)

    if st.button("🚀 PROCESSAR E GERAR EXCEL"):
        # Lógica de processamento simplificada para exportação
        st.success("Processamento concluído. (Simulação de Download)")
    st.markdown('</div>', unsafe_allow_html=True)
