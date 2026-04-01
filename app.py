import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS DEFINITIVO (CADASTRO TÉCNICO ESCURO) ---
st.markdown("""
    <style>
    /* Fundo Escuro para a aplicação toda para não dar erro de contraste */
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 98% !important; }

    /* MENU SUPERIOR ESTILO CRM AZUL */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px; background-color: #1a3a5a; padding: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px; color: #ffffff !important; font-weight: 500;
        border: none; background-color: transparent; padding: 0px 30px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c5282 !important; border-bottom: 3px solid #63b3ed !important;
    }

    /* FORÇAR ALTURA DOS CAMPOS BRANCOS */
    div[data-testid="stTextInput"] > div {
        min-height: 22px !important;
        height: 22px !important;
    }

    .stTextInput>div>div>input { 
        background-color: white !important; 
        color: black !important; 
        height: 22px !important; 
        text-transform: uppercase !important; 
        border-radius: 2px !important; 
        font-size: 11px !important;
        padding: 0px 8px !important;
    }
    
    /* LABELS VERDES LATERAIS ALINHADAS */
    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 11px !important; 
        margin-bottom: 0px !important;
        display: flex;
        align-items: center;
        height: 22px; 
    }
    
    /* ESPAÇAMENTO ENTRE LINHAS (O DOBRO QUE VOCÊ PEDIU) */
    [data-testid="stHorizontalBlock"] {
        margin-bottom: 8px !important;
    }

    /* BOTÕES VERDES LARGOS */
    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        height: 35px !important;
        border-radius: 4px !important;
        width: 100% !important;
    }

    /* CHECKBOXES VERDES */
    .stCheckbox label p { font-size: 11px !important; color: #2ecc71 !important; font-weight: bold; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- LÓGICA DE PAGAMENTO ---
def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with abas[0]:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    
    with col_central:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f", value=st.session_state.get("cidade_p", ""))
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.get("curso_acumulado", ""))
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f", value=st.session_state.get("vendedor_p", ""))
        campo_horizontal("DATA:", "data_input", value=st.session_state.get("data_p", ""))

        st.write("")
        # Checkboxes e Botões Centralizados
        sel1, sel2, sel3 = st.columns(3)
        with sel1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with sel2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with sel3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_field.upper(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with btn2:
            if st.button("FINALIZAR PDF"):
                if st.session_state.lista_previa:
                    df_sheets = conn.read(ttl="0s").fillna("")
                    df_novos = pd.DataFrame(st.session_state.lista_previa)
                    df_final = pd.concat([df_sheets, df_novos], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.rerun()

    # Tabela Branca de Prévia
    st.write("")
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=150)

with abas[1]:
    # Estilo de Gerenciamento CRM que você gostou
    st.write("### 🖥️ Base de Dados CRM")
    t1, t2 = st.columns([3, 1])
    with t1: busca = st.text_input("🔍 Filtrar...", label_visibility="collapsed").upper()
    with t2: 
        if st.button("🔄 Sync"): st.rerun()
    
    dados = conn.read(ttl="0s").fillna("")
    if busca:
        mask = dados.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
        dados = dados[mask]
    
    st.dataframe(dados, use_container_width=True, hide_index=True, height=600)
