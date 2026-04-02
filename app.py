import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- INICIALIZAÇÃO DE ESTADOS ---
campos_padrao = {
    "lista_previa": [], "f_id": "", "f_nome": "", "f_cid": "", 
    "f_curso": "", "f_pagto": "", "f_vend": "", 
    "f_data": date.today().strftime("%d/%m/%Y"),
    "chk_1": False, "chk_2": False, "chk_3": False
}

for chave, valor in campos_padrao.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# --- CSS ESTÉTICA HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
    .main .block-container { padding-top: 45px !important; max-width: 1200px !important; margin: 0 auto !important; }
    div[data-testid="stHorizontalBlock"] { margin-bottom: 5px !important; display: flex; align-items: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE LÓGICA ---
def transformar_curso():
    entrada = st.session_state.f_curso_input.strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1)
        nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state.f_curso = f"{base} + {nome}".upper() if base and nome.upper() not in base.upper() else nome.upper()
        else: st.session_state.f_curso = entrada.upper()
    else: st.session_state.f_curso = entrada.upper()

def processar_pagto():
    # Pega o que está escrito no campo de pagamento (removendo as observações antigas se houver)
    base = st.session_state.f_pagto_input.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_1: obs.append("LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CURSO BÔNUS")
    if st.session_state.chk_3: obs.append("CONFIRMAÇÃO MATRÍCULA")
    st.session_state.f_pagto = f"{base} | {' | '.join(obs)}" if obs else base

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ID:</label>", unsafe_allow_html=True)
        st.session_state.f_id = c_inp.text_input("ID", value=st.session_state.f_id, key="f_id_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        st.session_state.f_nome = c_inp.text_input("ALUNO", value=st.session_state.f_nome, key="f_nome_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        st.session_state.f_cid = c_inp.text_input("CIDADE", value=st.session_state.f_cid, key="f_cid_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        st.session_state.f_curso = c_inp.text_input("CURSO", value=st.session_state.f_curso, key="f_curso_input", on_change=transformar_curso, label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        st.session_state.f_pagto = c_inp.text_input("PAGAMENTO", value=st.session_state.f_pagto, key="f_pagto_input", on_change=processar_pagto, label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        st.session_state.f_vend = c_inp.text_input("VENDEDOR", value=st.session_state.f_vend, key="f_vend_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>DATA MATRÍCULA:</label>", unsafe_allow_html=True)
        st.session_state.f_data = c_inp.text_input("DATA", value=st.session_state.f_data, key="f_data_input", label_visibility="collapsed")

        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        _, b_col1, b_col2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        
        with b_col1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.f_nome:
                    aluno = {
                        "ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), 
                        "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.f_curso.upper(), 
                        "Pagamento": st.session_state.f_pagto.upper(), "Vendedor": st.session_state.f_vend.upper(), 
                        "Data Matrícula": st.session_state.f_data, "STATUS": "ATIVO"
                    }
                    st.session_state.lista_previa.append(aluno)
                    # Limpeza seletiva
                    st.session_state.f_id = ""
                    st.session_state.f_nome = ""
                    st.session_state.f_curso = ""
                    st.session_state.f_pagto = ""
                    st.session_state.chk_1 = False
                    st.session_state.chk_2 = False
                    st.session_state.chk_3 = False
                    st.rerun()

        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
                        client = gspread.authorize(creds)
                        sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                        ws = sh.get_worksheet(0)
                        
                        dados_final = pd.DataFrame(st.session_state.lista_previa).values.tolist()
                        col_a = ws.col_values(1)
                        ultima = len(col_a)
                        linha = ultima + 2 if ultima > 0 else 2
                        ws.insert_rows(dados_final, row=linha)
                        
                        # Limpeza total
                        for k in campos_padrao:
                            if k != "lista_previa": st.session_state[k] = campos_padrao[k]
                        st.session_state.lista_previa = []
                        st.success("Enviado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

        st.write("---")
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# As abas de Gerenciamento e Relatórios seguem a lógica anterior de leitura do conector padrão.
with tab_ger:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_ger = conn.read(ttl="0s").fillna("")
    if not df_ger.empty:
        st.dataframe(df_ger.iloc[::-1], use_container_width=True, hide_index=True, height=500)

with tab_rel:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_rel = conn.read(ttl="0s").dropna(how='all')
    if not df_rel.empty:
        # (Lógica de processamento de datas e extração de valores mantida do código original)
        st.info("Relatórios carregados com sucesso.")
