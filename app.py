import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA ALINHAMENTO MILIMÉTRICO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 98% !important; }

    /* Estilo dos Inputs */
    div[data-testid="stTextInput"] > div { min-height: 24px !important; height: 24px !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 24px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 12px !important; padding: 0px 8px !important;
    }
    
    /* Labels Verdes Laterais */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 12px !important; 
        display: flex; align-items: center; height: 24px; justify-content: flex-end; padding-right: 15px;
    }
    
    /* Botões Principais Centralizados e Compactos */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 35px !important; font-size: 13px !important;
        border-radius: 4px !important; border: none !important;
        width: 200px !important; margin: 0 auto !important; display: block !important;
    }

    /* REMOVENDO O GAP DE 1KM DOS CHECKBOXES */
    /* Forçamos os itens a ficarem juntos no centro */
    div[data-testid="column"] { 
        display: flex !important; 
        justify-content: center !important; 
        width: auto !important;
        min-width: fit-content !important;
        flex: 0 1 auto !important;
        gap: 10px !important;
    }
    
    .stCheckbox { margin-right: 20px !important; }
    .stCheckbox label p { 
        font-size: 11px !important; color: #2ecc71 !important; 
        font-weight: bold; white-space: nowrap;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; border: 1px solid #ddd; }
    [data-testid="stHorizontalBlock"] { gap: 10px !important; justify-content: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E LOGICA ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 3]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

def atualizar_pagto():
    texto = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: texto += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: texto += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: texto += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = texto

# --- INTERFACE ---
abas = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

with abas[0]:
    # Centraliza o formulário num bloco de largura fixa
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado)
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        st.write("")
        
        # --- BLOCO DE CHECKBOXES JUNTOS E CENTRALIZADOS ---
        # Criamos colunas pequenas apenas para os textos não espalharem
        c_check = st.columns([1, 1, 1.2]) 
        with c_check[0]: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c_check[1]: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c_check[2]: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        st.write("")
        
        # --- BOTÕES DE AÇÃO LADO A LADO ---
        c_btns = st.columns(2)
        with c_btns[0]:
            if st.button("SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_field.upper(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.curso_field = ""
                    st.session_state.pagto_input = ""
                    st.session_state.check_lib = False
                    st.session_state.check_bonus = False
                    st.session_state.check_conf = False
                    st.rerun()
        
        with c_btns[1]:
            if st.button("FINALIZAR PDF"):
                if st.session_state.lista_previa:
                    st.session_state.lista_previa = []
                    st.rerun()

    # Tabela de Pré-visualização embaixo, ocupando a largura total
    st.markdown("<br>", unsafe_allow_html=True)
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True)

with abas[1]:
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True)
