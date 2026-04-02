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
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# Chaves para limpeza controlada
campos_para_limpar = ["f_id", "f_nome", "input_curso_key", "input_pagto_key"]
for campo in campos_para_limpar:
    if campo not in st.session_state: st.session_state[campo] = ""

# Campos que permanecem (só zeram no envio)
campos_permanentes = ["f_cid", "f_vend"]
for campo in campos_permanentes:
    if campo not in st.session_state: st.session_state[campo] = ""
if "f_data" not in st.session_state: st.session_state.f_data = date.today().strftime("%d/%m/%Y")

# --- CSS ESTÉTICA HUD NEON (Mantido igual) ---
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
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def extrair_valor_recebido(texto):
    texto = str(texto).upper()
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', texto)
    if match:
        v = match.group(1).replace('.', '').replace(',', '.')
        try: return float(v)
        except: return 0.0
    return 0.0

def extrair_valor_geral(texto):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def transformar_curso():
    entrada = st.session_state.input_curso_key.strip()
    if not entrada: st.session_state.val_curso = ""; return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state.val_curso = f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)
        else: st.session_state.val_curso = entrada.upper()
    else: st.session_state.val_curso = entrada.upper()
    st.session_state.val_curso = st.session_state.val_curso.upper().strip() + " "
    st.session_state.input_curso_key = st.session_state.val_curso

def processar_pagto():
    base = st.session_state.input_pagto_key.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.get('chk_1'): obs.append("LIBERAÇÃO IN-GLÊS")
    if st.session_state.get('chk_2'): obs.append("CURSO BÔNUS")
    if st.session_state.get('chk_3'): obs.append("CONFIRMAÇÃO MATRÍCULA")
    st.session_state.val_pagto = f"{base} | {' | '.join(obs)}" if obs else base
    st.session_state.input_pagto_key = st.session_state.val_pagto

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        # Layout de Campos
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ID:</label>", unsafe_allow_html=True)
        st.session_state.f_id = c_inp.text_input("ID", key="f_id_input", value=st.session_state.f_id, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        st.session_state.f_nome = c_inp.text_input("ALUNO", key="f_nome_input", value=st.session_state.f_nome, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        st.session_state.f_cid = c_inp.text_input("CIDADE", key="f_cid_input", value=st.session_state.f_cid, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        st.session_state.input_curso_key = c_inp.text_input("CURSO", key="f_curso_input", value=st.session_state.input_curso_key, on_change=transformar_curso, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        st.session_state.input_pagto_key = c_inp.text_input("PAGAMENTO", key="f_pagto_input", value=st.session_state.input_pagto_key, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        st.session_state.f_vend = c_inp.text_input("VENDEDOR", key="f_vend_input", value=st.session_state.f_vend, label_visibility="collapsed")
        
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>DATA MATRÍCULA:</label>", unsafe_allow_html=True)
        st.session_state.f_data = c_inp.text_input("DATA", key="f_data_input", value=st.session_state.f_data, label_visibility="collapsed")

        # Checkboxes
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
                        "ID": st.session_state.f_id.upper(), 
                        "Aluno": st.session_state.f_nome.upper(), 
                        "Cidade": st.session_state.f_cid.upper(), 
                        "Curso": st.session_state.input_curso_key.strip().upper(), 
                        "Pagamento": st.session_state.input_pagto_key.upper(), 
                        "Vendedor": st.session_state.f_vend.upper(), 
                        "Data Matrícula": st.session_state.f_data, 
                        "STATUS": "ATIVO"
                    }
                    st.session_state.lista_previa.append(aluno)
                    
                    # LIMPA APENAS OS CAMPOS SOLICITADOS
                    st.session_state.f_id = ""
                    st.session_state.f_nome = ""
                    st.session_state.input_curso_key = ""
                    st.session_state.input_pagto_key = ""
                    st.session_state.val_curso = ""
                    st.session_state.val_pagto = ""
                    st.rerun()

        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        worksheet = sh.get_worksheet(0)
                        
                        novos_dados = pd.DataFrame(st.session_state.lista_previa).values.tolist()
                        ultima = len(worksheet.col_values(1))
                        linha_destino = ultima + 2 if ultima > 0 else 2
                        worksheet.insert_rows(novos_dados, row=linha_destino)
                        
                        # ZERA TUDO AGORA
                        st.session_state.lista_previa = []
                        st.session_state.f_id = ""
                        st.session_state.f_nome = ""
                        st.session_state.f_cid = "" # Zera Cidade
                        st.session_state.input_curso_key = ""
                        st.session_state.input_pagto_key = ""
                        st.session_state.f_vend = "" # Zera Vendedor
                        st.session_state.f_data = date.today().strftime("%d/%m/%Y") # Reseta Data
                        
                        st.success("Enviado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.write("---")
        if st.session_state.lista_previa:
            st.markdown("<p style='color:#00f2ff; font-weight:bold; text-align:center;'>PRÉ-VISUALIZAÇÃO</p>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# (Aba de Gerenciamento e Relatórios permanecem as mesmas do código anterior)
