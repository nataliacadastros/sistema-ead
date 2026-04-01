import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ULTRA COMPACTO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 98% !important; }

    /* Inputs e Labels */
    div[data-testid="stTextInput"] > div { min-height: 22px !important; height: 22px !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 22px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 11px !important; padding: 0px 5px !important;
    }
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; height: 22px; justify-content: flex-end; padding-right: 10px;
    }
    
    /* Botões Verdes */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 30px !important; font-size: 12px !important;
    }

    /* Tabs e Checkboxes */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #004a99; padding: 2px 10px; }
    .stCheckbox label p { font-size: 10px !important; color: #2ecc71 !important; font-weight: bold; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; }
    [data-testid="stHorizontalBlock"] { margin-bottom: 4px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTADOS ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- LÓGICA DE PAGAMENTO DINÂMICO ---
def atualizar_pagto():
    # 1. Pega o que está escrito no campo, mas remove qualquer sufixo anterior (o que vem depois do |)
    texto_atual = st.session_state.pagto_input
    base = texto_atual.split(" | ")[0].strip().upper()
    
    # 2. Reconstrói o texto com base nos botões marcados
    if st.session_state.check_lib:
        base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus:
        base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf:
        base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    
    # 3. Atualiza o valor do campo de texto
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
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    with col_form:
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado, on_change=processar_curso)
        
        # Campo de Pagamento
        campo_horizontal("PAGAMENTO:", "pagto_input")
        
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        st.write("")
        # Botões de Seleção (Checkboxes) que disparam a atualização
        c1, c2, c3, b1, b2 = st.columns([1.2, 1.2, 1.2, 1.5, 1.5])
        with c1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        if b1.button("SALVAR ALUNO"):
            if st.session_state.nome_alu:
                aluno = {
                    "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                    "Cidade": st.session_state.cid_f.upper(), "Curso Contratado": st.session_state.curso_acumulado,
                    "Forma de Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                    "Data": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno)
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("FINALIZAR PDF"):
            if st.session_state.lista_previa:
                # Lógica simplificada de envio
                df_at = conn.read(ttl="0s").fillna("")
                df_nv = pd.DataFrame(st.session_state.lista_previa)
                df_fi = pd.concat([df_at, df_nv], ignore_index=True)
                conn.update(data=df_fi)
                st.session_state.lista_previa = []
                st.rerun()

    # Tabela de Pré-visualização
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=150)

with abas[1]:
    st.subheader("Gerenciamento")
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True)
