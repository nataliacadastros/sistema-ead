import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA TELA ÚNICA (COLUNA ÚNICA) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; overflow-y: hidden; }
    
    /* Preenchimento total e sem respiros */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }

    /* Inputs Super Compactos */
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 12px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 11px !important;
        padding: 2px 5px !important;
    }
    
    /* Labels Coladas e Verdes */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; 
        font-size: 10px !important; margin-bottom: -10px !important; 
        padding-top: 0px !important;
    }
    
    /* Checkboxes e Botões */
    .stCheckbox { margin-top: -10px !important; }
    .stCheckbox label p { font-size: 10px !important; }

    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        height: 28px !important;
        font-size: 11px !important;
        border-radius: 3px !important;
        margin-top: 10px !important;
    }

    /* Menu Superior */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #004a99; padding: 2px 10px; }
    .stTabs [data-baseweb="tab"] { height: 28px; font-size: 11px !important; color: white !important; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Tabela Branca com Altura Fixa */
    .stDataFrame { background-color: white !important; border-radius: 0px !important; }
    
    /* Reduz gap entre todos os elementos */
    [data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

COLUNAS_TABELA = ["ID", "Aluno", "Tel. Responsável", "Tel. Aluno", "CPF Responsável", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data da Matrícula"]

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

for key in ["lista_previa", "curso_acumulado", "cidade_p", "vendedor_p", "data_p"]:
    if key not in st.session_state: st.session_state[key] = ""
if "lista_previa" not in st.session_state or st.session_state.lista_previa == "": 
    st.session_state.lista_previa = []

# --- FUNÇÕES DE LÓGICA ---
def aplicar_mascara_cpf():
    v = "".join(filter(str.isdigit, st.session_state.cpf_input))
    if len(v) == 11: st.session_state.cpf_input = f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"

def aplicar_mascara_data():
    v = "".join(filter(str.isdigit, st.session_state.data_input))
    if len(v) == 8: st.session_state.data_input = f"{v[:2]}/{v[2:4]}/{v[4:]}"

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

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- MENU SUPERIOR ---
aba_selecionada = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

with aba_selecionada[0]:
    # COLUNA ÚNICA CENTRALIZADA
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        st.text_input("ID", key="id_alu")
        st.text_input("Aluno", key="nome_alu")
        st.text_input("Tel. Responsável", key="t_resp")
        st.text_input("Tel. Aluno", key="t_alu")
        st.text_input("CPF Responsável", key="cpf_input", on_change=aplicar_mascara_cpf)
        st.text_input("Cidade", value=st.session_state.cidade_p, key="cid_f")
        st.text_input("Curso Contratado", value=st.session_state.curso_acumulado, key="curso_field", on_change=processar_curso)
        st.text_input("Forma de Pagamento", key="pagto_input")
        st.text_input("Vendedor", value=st.session_state.vendedor_p, key="vend_f")
        st.text_input("Data da Matrícula", value=st.session_state.data_p, key="data_input", on_change=aplicar_mascara_data)

        # Controles e Botões em uma única linha compacta
        c1, c2, c3, b1, b2 = st.columns([1, 1, 1, 1.2, 1.2])
        with c1: st.checkbox("IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c2: st.checkbox("BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c3: st.checkbox("CONFIRMA", key="check_conf", on_change=atualizar_pagto)

        if b1.button("SALVAR"):
            if st.session_state.nome_alu:
                aluno_novo = {
                    "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(), 
                    "Tel. Responsável": st.session_state.t_resp, "Tel. Aluno": st.session_state.t_alu, 
                    "CPF Responsável": st.session_state.cpf_input, "Cidade": st.session_state.cid_f.upper(), 
                    "Curso Contratado": st.session_state.curso_acumulado.strip(),
                    "Forma de Pagamento": st.session_state.pagto_input.upper(),
                    "Vendedor": st.session_state.vend_f.upper(), "Data da Matrícula": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno_novo)
                st.session_state.cidade_p = st.session_state.cid_f.upper()
                st.session_state.vendedor_p = st.session_state.vend_f.upper()
                st.session_state.data_p = st.session_state.data_input
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("FINALIZAR"):
            if st.session_state.lista_previa:
                # Lógica de salvamento...
                st.session_state.lista_previa = []
                st.session_state.cidade_p = ""; st.session_state.vendedor_p = ""; st.session_state.data_p = ""
                st.rerun()

    # --- TABELA DE PRÉ-VISUALIZAÇÃO (OCUPANDO O RESTANTE DA TELA) ---
    st.markdown(f"<p style='text-align: center; margin-bottom: 0px; font-size: 11px;'>Lista: {len(st.session_state.lista_previa)}</p>", unsafe_allow_html=True)
    
    if st.session_state.lista_previa:
        df_visual = pd.DataFrame(st.session_state.lista_previa)[COLUNAS_TABELA]
    else:
        df_visual = pd.DataFrame([[""]*len(COLUNAS_TABELA)], columns=COLUNAS_TABELA)
    
    # Altura pequena (150) para garantir que não precise de scroll
    st.dataframe(df_visual, use_container_width=True, hide_index=True, height=150)
