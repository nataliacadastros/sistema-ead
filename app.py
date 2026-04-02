import streamlit as st
import pandas as pd
import re
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- INICIALIZAÇÃO DE VARIÁVEIS DE PERSONALIZAÇÃO ---
if "cfg_input_height" not in st.session_state: st.session_state.cfg_input_height = 25
if "cfg_input_width" not in st.session_state: st.session_state.cfg_input_width = 100

# --- CSS DINÂMICO ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #1a2436; color: white; }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: #1a3a5a; border-bottom: 2px solid #2c5282; }}
    .stTabs [data-baseweb="tab"] {{ color: #ffffff !important; font-weight: 600; padding: 0px 30px; }}
    .stTabs [aria-selected="true"] {{ background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important; }}
    
    /* ESTE É O BLOCO QUE VOCÊ ESTÁ AJUSTANDO */
    div[data-testid="stTextInput"] > div {{ 
        min-height: {st.session_state.cfg_input_height}px !important; 
        height: {st.session_state.cfg_input_height}px !important;
        width: {st.session_state.cfg_input_width}% !important;
    }}
    .stTextInput input {{ background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; }}
    
    label {{ 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; justify-content: flex-end; padding-right: 15px; height: {st.session_state.cfg_input_height}px;
    }}
    
    .stCheckbox label p {{ color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; white-space: nowrap; }}
    
    div.stButton > button {{
        background-color: #2ecc71 !important; color: white !important; font-weight: bold !important;
        height: 40px !important; width: 100% !important; border: none !important; border-radius: 5px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        white-space: nowrap !important; font-size: 13px !important;
    }}
    
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# --- FUNÇÕES ---
def transformar_curso():
    entrada = st.session_state.input_curso_key.strip()
    if not entrada: st.session_state.val_curso = ""; st.session_state.input_curso_key = ""; return
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
    if st.session_state.chk_1: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if st.session_state.chk_3: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    st.session_state.val_pagto = f"{base} | {' | '.join(obs)}" if obs else base
    st.session_state.input_pagto_key = st.session_state.val_pagto

# --- UI ---
tab_cad, tab_ger, tab_rel, tab_cfg = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "⚙️ AJUSTES"])

with tab_cad:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    with col_central:
        st.write("")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ID:</label>", unsafe_allow_html=True); c2.text_input("ID", key="f_id", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ALUNO:</label>", unsafe_allow_html=True); c2.text_input("ALUNO", key="f_nome", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CIDADE:</label>", unsafe_allow_html=True); c2.text_input("CIDADE", key="f_cid", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CURSO:</label>", unsafe_allow_html=True); c2.text_input("CURSO", key="input_curso_key", value=st.session_state.val_curso, on_change=transformar_curso, label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True); c2.text_input("PAGAMENTO", key="input_pagto_key", value=st.session_state.val_pagto, label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True); c2.text_input("VENDEDOR", key="f_vend", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>DATA:</label>", unsafe_allow_html=True); c2.text_input("DATA", key="f_data", value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")

        st.write("")
        recuo, area_botoes = st.columns([1.2, 4])
        with area_botoes:
            s1, s2, s3 = st.columns(3)
            with s1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
            with s2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
            with s3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        recuo_btn, area_acao = st.columns([1.2, 4])
        with area_acao:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 SALVAR ALUNO"):
                    if st.session_state.f_nome:
                        aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), "Data": st.session_state.f_data}
                        st.session_state.lista_previa.append(aluno); st.session_state.val_curso = ""; st.session_state.val_pagto = ""; st.session_state.f_nome = ""; st.session_state.f_id = ""; st.rerun()
            with b2:
                if st.button("📤 ENVIAR PLANILHA"):
                    if st.session_state.lista_previa:
                        df_old = conn.read(ttl="0s").fillna(""); df_new = pd.DataFrame(st.session_state.lista_previa); conn.update(data=pd.concat([df_old, df_new], ignore_index=True)); st.session_state.lista_previa = []; st.success("Enviado!"); st.rerun()

# --- ABA DE AJUSTES ---
with tab_cfg:
    st.subheader("⚙️ Ajustes dos Campos de Texto")
    
    st.session_state.cfg_input_height = st.slider("Altura (px)", 20, 100, st.session_state.cfg_input_height)
    st.session_state.cfg_input_width = st.slider("Largura (%)", 10, 100, st.session_state.cfg_input_width)
    
    st.write("---")
    st.write("### 📋 COPIE O CÓDIGO ABAIXO E ME ENVIE:")
    
    # Gera o texto do código para você me enviar
    codigo_gerado = f"""
div[data-testid="stTextInput"] > div {{ 
    min-height: {st.session_state.cfg_input_height}px !important; 
    height: {st.session_state.cfg_input_height}px !important;
    width: {st.session_state.cfg_input_width}% !important;
}}
"""
    st.code(codigo_gerado, language="css")

with tab_ger:
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=600)
    except: st.error("Erro ao carregar banco de dados.")
