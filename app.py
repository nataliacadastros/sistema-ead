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

# --- CSS PARA MENU FINO E CONTEÚDO COLADO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    /* MENU DE NAVEGAÇÃO MAIS FINO (SLIM) */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a3a5a; 
        border-bottom: 2px solid #2c5282;
        position: fixed;
        top: 0;
        left: 0 !important;
        width: 100vw !important;
        z-index: 999;
        justify-content: center;
        height: 30px !important; /* Altura reduzida do menu */
    }

    .stTabs [data-baseweb="tab"] { 
        color: #ffffff !important; 
        font-weight: 600; 
        padding: 0px 30px !important;
        height: 30px !important; /* Mesma altura do fundo */
        line-height: 30px !important; /* Centraliza o texto verticalmente */
        font-size: 13px !important;
    }

    .stTabs [aria-selected="true"] { 
        border-bottom: 3px solid #2ecc71 !important; 
    }
    
    /* CONTEÚDO COLADO NO MENU FINO */
    .main .block-container { 
        padding-top: 32px !important; /* 30px do menu + 2px de folga */
        padding-bottom: 0px !important;
    }

    /* Remove espaços extras entre widgets */
    [data-testid="stVerticalBlock"] > div {
        gap: 0rem !important;
    }

    /* Inputs (Seus Ajustes) */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 2px !important; }
    div[data-testid="stTextInput"] > div { 
        min-height: 25px !important; height: 25px !important;
        width: 55% !important;
    }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; }

    /* Labels */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 15px !important; 
        padding-right: 2px !important; height: 25px !important;
        display: flex; align-items: center; justify-content: flex-end;
    }
    
    /* Checkboxes e Botões */
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; white-space: nowrap; }
    
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important; font-weight: bold !important;
        height: 40px !important; border: none !important; border-radius: 5px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        white-space: nowrap !important; font-size: 13px !important; padding: 0px 20px !important;
    }

    /* Lista de Prévia */
    hr { margin-top: 5px !important; margin-bottom: 5px !important; }
    .contador-estilo {
        text-align: right;
        color: #2ecc71;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 2px;
        padding-right: 5px;
    }
    div[data-testid="stDataFrame"] { margin-top: -10px !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
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

# --- UI PRINCIPAL ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    
    with col_central:
        # Formulário de Cadastro
        for label, key, func in [
            ("ID:", "f_id", None), ("ALUNO:", "f_nome", None), ("CIDADE:", "f_cid", None),
            ("CURSO:", "input_curso_key", transformar_curso), ("PAGAMENTO:", "input_pagto_key", None),
            ("VENDEDOR:", "f_vend", None), ("DATA:", "f_data", None)
        ]:
            c1, c2 = st.columns([1.2, 4])
            c1.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if key == "input_curso_key":
                c2.text_input(label, key=key, value=st.session_state.val_curso, on_change=func, label_visibility="collapsed")
            elif key == "input_pagto_key":
                c2.text_input(label, key=key, value=st.session_state.val_pagto, label_visibility="collapsed")
            elif key == "f_data":
                c2.text_input(label, key=key, value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")
            else:
                c2.text_input(label, key=key, label_visibility="collapsed")

        st.write("")
        recuo, area_checks = st.columns([1.2, 4])
        with area_checks:
            s1, s2, s3 = st.columns(3)
            with s1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
            with s2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
            with s3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        recuo_btn, area_btns = st.columns([1.2, 4])
        with area_btns:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 SALVAR ALUNO"):
                    if st.session_state.f_nome:
                        aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), "Data": st.session_state.f_data}
                        st.session_state.lista_previa.append(aluno)
                        st.rerun()
            with b2:
                if st.button("📤 ENVIAR PLANILHA"):
                    if st.session_state.lista_previa:
                        df_old = conn.read(ttl="0s").fillna(""); df_new = pd.DataFrame(st.session_state.lista_previa); conn.update(data=pd.concat([df_old, df_new], ignore_index=True)); st.session_state.lista_previa = []; st.success("Enviado!"); st.rerun()

        # --- LISTA DE PRÉ-VISUALIZAÇÃO IMEDIATA ---
        st.write("---") 
        qtd = len(st.session_state.lista_previa)
        st.markdown(f'<div class="contador-estilo">Alunos Salvos: {qtd}</div>', unsafe_allow_html=True)
        
        df_previa = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
        st.dataframe(df_previa, use_container_width=True, hide_index=True)

with tab_ger:
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=600)
    except: st.error("Erro ao carregar banco de dados.")
