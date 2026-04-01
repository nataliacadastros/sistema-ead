import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA CENTRALIZAÇÃO TOTAL ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 98% !important; }

    /* Estilo dos Inputs */
    div[data-testid="stTextInput"] > div { min-height: 22px !important; height: 22px !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 22px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 11px !important; padding: 0px 5px !important;
    }
    
    /* Labels Verdes Laterais */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; height: 22px; justify-content: flex-end; padding-right: 10px;
    }
    
    /* Botões Verdes Principais */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 38px !important; font-size: 13px !important;
        border-radius: 4px !important; border: none !important;
    }

    /* Centralização dos Checkboxes */
    .stCheckbox { display: flex; justify-content: center; }
    .stCheckbox label p { 
        font-size: 10px !important; color: #2ecc71 !important; 
        font-weight: bold; white-space: nowrap; margin-left: -5px;
    }
    
    /* Ajuste de colunas para botões de seleção */
    [data-testid="column"] { display: flex; justify-content: center; align-items: center; }

    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; }
    [data-testid="stHorizontalBlock"] { margin-bottom: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- LÓGICA DE PAGAMENTO ---
def atualizar_pagto():
    texto_atual = st.session_state.pagto_input
    base = texto_atual.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- LÓGICA DE CURSO ---
def processar_curso():
    texto = st.session_state.curso_field.strip()
    partes = texto.split()
    if partes:
        ultimo = partes[-1]
        if ultimo in CURSOS_DICT:
            nome = CURSOS_DICT[ultimo].upper()
            anterior = " ".join(partes[:-1])
            st.session_state.curso_acumulado = f"{anterior} + {nome} " if anterior else f"{nome} "
        else: st.session_state.curso_acumulado = texto.upper() + " "
    st.session_state.curso_field = st.session_state.curso_acumulado

# --- INTERFACE ---
abas = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

with abas[0]:
    # Coluna central para o formulário
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    
    with col_form:
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado, on_change=processar_curso)
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        st.write("")
        
        # --- CENTRALIZAÇÃO DOS CHECKBOXES ---
        # Criamos colunas extras nas laterais para empurrar o conteúdo para o meio
        _, c_sel, _ = st.columns([0.5, 3, 0.5])
        with c_sel:
            sel1, sel2, sel3 = st.columns(3)
            with sel1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
            with sel2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
            with sel3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        # --- CENTRALIZAÇÃO DOS BOTÕES PRINCIPAIS ---
        _, c_btn, _ = st.columns([0.2, 2, 0.2])
        with c_btn:
            btn1, btn2 = st.columns(2)
            if btn1.button("SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_acumulado.strip(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.curso_acumulado = ""
                    st.session_state.pagto_input = ""
                    st.session_state.check_lib = False
                    st.session_state.check_bonus = False
                    st.session_state.check_conf = False
                    st.rerun()

            if btn2.button("FINALIZAR PDF"):
                if st.session_state.lista_previa:
                    st.session_state.lista_previa = []
                    st.rerun()

    # Tabela
    st.markdown("---")
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=160)

with abas[1]:
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True)
