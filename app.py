import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ULTRA COMPACTO (CORREÇÃO DO ERRO) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; overflow: hidden; }
    
    /* Reduzindo margens da página */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }

    /* FORÇANDO ALTURA DOS CAMPOS (O segredo está no min-height do container) */
    div[data-testid="stTextInput"] > div {
        min-height: 20px !important;
        height: 20px !important;
    }

    .stTextInput>div>div>input { 
        background-color: white !important; 
        color: black !important; 
        height: 20px !important; 
        min-height: 20px !important;
        line-height: 20px !important;
        text-transform: uppercase !important; 
        border-radius: 2px !important; 
        font-size: 11px !important;
        padding: 0px 5px !important;
    }
    
    /* Labels Verdes e Coladas */
    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 10px !important; 
        margin-bottom: -12px !important; 
    }
    
    /* Botões Verdes Pequenos */
    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        height: 28px !important;
        font-size: 11px !important;
        border-radius: 3px !important;
    }

    /* Menu Superior */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #004a99; padding: 2px 10px; }
    .stTabs [data-baseweb="tab"] { height: 28px; font-size: 11px !important; color: white !important; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Tabela Branca */
    .stDataFrame { background-color: white !important; border-radius: 0px !important; }
    
    /* Remove espaços entre blocos verticais */
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DICIONÁRIO E CONFIGURAÇÕES ---
CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}
COLUNAS = ["ID", "Aluno", "Tel. Responsável", "Tel. Aluno", "CPF Responsável", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data da Matrícula"]

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""
if "cidade_p" not in st.session_state: st.session_state.cidade_p = ""
if "vendedor_p" not in st.session_state: st.session_state.vendedor_p = ""
if "data_p" not in st.session_state: st.session_state.data_p = ""

# --- FUNÇÕES DE APOIO ---
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

# --- NAVEGAÇÃO ---
abas = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

with abas[0]:
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

        # Controles em linha única
        c1, c2, c3, b1, b2 = st.columns([1, 1, 1, 1.5, 1.5])
        with c1: st.checkbox("IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c2: st.checkbox("BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c3: st.checkbox("CONFIRMA", key="check_conf", on_change=atualizar_pagto)

        if b1.button("SALVAR"):
            if st.session_state.nome_alu:
                aluno = {
                    "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(), 
                    "Tel. Responsável": st.session_state.t_resp, "Tel. Aluno": st.session_state.t_alu, 
                    "CPF Responsável": st.session_state.cpf_input, "Cidade": st.session_state.cid_f.upper(), 
                    "Curso Contratado": st.session_state.curso_acumulado.strip(),
                    "Forma de Pagamento": st.session_state.pagto_input.upper(),
                    "Vendedor": st.session_state.vend_f.upper(), "Data da Matrícula": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno)
                st.session_state.cidade_p = st.session_state.cid_f.upper()
                st.session_state.vendedor_p = st.session_state.vend_f.upper()
                st.session_state.data_p = st.session_state.data_input
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("FINALIZAR"):
            if st.session_state.lista_previa:
                # Aqui iria sua lógica de salvar no GSheets
                st.session_state.lista_previa = []
                st.success("Enviado!")
                st.rerun()

    # Tabela Branca Fixa
    if st.session_state.lista_previa:
        df_vis = pd.DataFrame(st.session_state.lista_previa)[COLUNAS]
    else:
        df_vis = pd.DataFrame([[""]*len(COLUNAS)], columns=COLUNAS)
    
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=120)

with abas[1]:
    st.write("Gerenciamento")

with abas[2]:
    st.write("Relatórios")
