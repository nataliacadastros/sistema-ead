import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA DESIGN PROFISSIONAL E CENTRALIZAÇÃO TOTAL ---
st.markdown("""
    <style>
    /* Fundo e Container Geral */
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0rem !important; max-width: 100% !important; }

    /* MENU SUPERIOR (TABS) PROFISSIONAL */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #0d1626;
        padding: 0px 20px;
        border-bottom: 2px solid #004a99;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre;
        color: #8a9ab0 !important;
        background-color: transparent;
        font-weight: bold;
        border: none;
        padding: 0px 25px;
    }
    .stTabs [aria-selected="true"] {
        color: #2ecc71 !important;
        background-color: #1a2436 !important;
        border-bottom: 3px solid #2ecc71 !important;
    }

    /* CAMPOS DE PREENCHIMENTO */
    div[data-testid="stTextInput"] > div { min-height: 26px !important; height: 26px !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 26px !important; text-transform: uppercase !important; 
        border-radius: 4px !important; font-size: 13px !important; padding: 0px 10px !important;
    }
    
    /* LABELS LATERAIS */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 12px !important; 
        display: flex; align-items: center; height: 26px; justify-content: flex-end; padding-right: 15px;
    }
    
    /* BOTÕES DE AÇÃO - LARGURA IGUAL AOS CAMPOS */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 40px !important; font-size: 14px !important;
        border-radius: 4px !important; border: none !important;
        width: 100% !important; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #27ae60 !important; transform: scale(1.02); }

    /* CHECKBOXES CENTRALIZADOS E GRUDADOS */
    [data-testid="stHorizontalBlock"].css-1p0mha4  { justify-content: center !important; }
    .stCheckbox { display: flex; justify-content: center; }
    .stCheckbox label p { 
        font-size: 12px !important; color: #2ecc71 !important; 
        font-weight: bold; white-space: nowrap; margin-top: 2px;
    }
    
    /* REMOVER ELEMENTOS STREAMLIT */
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 2.5]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "📊 GERENCIAMENTO", "📈 RELATÓRIOS"])

with abas[0]:
    # Centralização Máxima do Bloco de Formulário
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.write("") 
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado)
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        # Checkboxes Centralizados e próximos (Usando colunas para agrupar no meio)
        st.write("")
        c_sel = st.columns([1, 1, 1.2])
        with c_sel[0]: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c_sel[1]: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c_sel[2]: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        # Botões de Ação ocupando a mesma largura do formulário
        st.write("")
        c_btns = st.columns(2)
        with c_btns[0]:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_field.upper(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.curso_field = ""; st.session_state.pagto_input = ""
                    st.session_state.check_lib = False; st.session_state.check_bonus = False; st.session_state.check_conf = False
                    st.rerun()
        
        with c_btns[1]:
            if st.button("📄 FINALIZAR PDF"):
                if st.session_state.lista_previa:
                    st.session_state.lista_previa = []
                    st.rerun()

    # Tabela ocupa a largura total para visualização clara
    st.markdown("<br>", unsafe_allow_html=True)
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True)

with abas[1]:
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True)
