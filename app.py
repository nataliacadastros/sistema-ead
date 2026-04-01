import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS REFINADO COM MAIS ESPAÇAMENTO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }

    /* Altura dos campos mantida em 22px para precisão */
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
    
    /* Labels Verdes com Alinhamento e Espaço */
    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 11px !important; 
        margin-bottom: 0px !important;
        display: flex;
        align-items: center;
        height: 22px; 
    }
    
    /* O SEGREDO DO ESPAÇO: Aumentando o gap entre as colunas e margem das linhas */
    [data-testid="stHorizontalBlock"] {
        margin-bottom: 8px !important; /* Aqui dobramos o espaço vertical entre as linhas */
    }

    /* Botões Verdes */
    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        height: 35px !important;
        border-radius: 4px !important;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { background-color: #004a99; padding: 5px; }
    .stDataFrame { background-color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- FUNÇÃO DE CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    # Proporção [1.2, 4] para dar um pouco mais de respiro ao texto do label
    c1, c2 = st.columns([1.2, 4]) 
    with c1:
        st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2:
        return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- PROCESSAMENTO DE CURSO ---
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
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    
    with col_central:
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f", value=st.session_state.get("cidade_p", ""))
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.get("curso_acumulado", ""), on_change=processar_curso)
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f", value=st.session_state.get("vendedor_p", ""))
        campo_horizontal("DATA MATRÍCULA:", "data_input", value=st.session_state.get("data_p", ""))

        st.write("")
        # Checkboxes e Botões
        c1, c2, c3, b1, b2 = st.columns([1, 1, 1, 1.5, 1.5])
        with c1: st.checkbox("IN-GLÊS", key="check_lib")
        with c2: st.checkbox("BÔNUS", key="check_bonus")
        with c3: st.checkbox("CONFIRMA", key="check_conf")

        if b1.button("SALVAR ALUNO"):
            if st.session_state.nome_alu:
                aluno = {
                    "ID": st.session_state.id_alu.upper(),
                    "Aluno": st.session_state.nome_alu.upper(),
                    "Cidade": st.session_state.cid_f.upper(),
                    "Curso Contratado": st.session_state.get("curso_acumulado", ""),
                    "Forma de Pagamento": st.session_state.pagto_input.upper(),
                    "Vendedor": st.session_state.vend_f.upper(),
                    "Data": st.session_state.data_input
                }
                if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
                st.session_state.lista_previa.append(aluno)
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("FINALIZAR PDF"):
            st.session_state.lista_previa = []
            st.rerun()

    # Tabela de Pré-visualização
    st.markdown("---")
    if "lista_previa" in st.session_state and st.session_state.lista_previa:
        st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)
    else:
        # Tabela branca "vazia" com os nomes das colunas
        cols = ["ID", "Aluno", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data"]
        st.dataframe(pd.DataFrame(columns=cols), use_container_width=True, hide_index=True)
