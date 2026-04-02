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

# --- CSS CONSOLIDADO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    /* MENU SLIM NO TOPO */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a3a5a; 
        border-bottom: 2px solid #2c5282;
        position: fixed;
        top: 0;
        left: 0 !important;
        width: 100vw !important;
        z-index: 999;
        justify-content: center;
        height: 32px !important;
    }
    .stTabs [data-baseweb="tab"] { 
        color: #ffffff !important; font-weight: 600; padding: 0px 30px !important;
        height: 32px !important; line-height: 32px !important; font-size: 13px !important;
    }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #2ecc71 !important; }
    
    /* CONTEÚDO COLADO NO TOPO */
    .main .block-container { 
        padding-top: 38px !important; 
        max-width: 1100px !important;
        margin: 0 auto !important;
    }

    /* CONFIGURAÇÃO DOS CAMPOS */
    div[data-testid="stHorizontalBlock"] { 
        margin-bottom: 3px !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    div[data-testid="stTextInput"] > div { 
        min-height: 25px !important; 
        height: 25px !important;
        width: 100% !important;
    }

    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 15px !important; 
        padding-right: 15px !important; 
        height: 25px !important;
        display: flex; 
        align-items: center; 
        justify-content: flex-end;
    }

    .stTextInput input { 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        font-size: 12px !important;
        height: 25px !important;
        border-radius: 5px !important;
    }

    /* Checkboxes e Botões Grandes (Cadastro) */
    .stCheckbox { display: flex; justify-content: center; margin-top: 8px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    
    .stButton > button {
        background-color: #2ecc71 !important; color: white !important; font-weight: bold !important;
        border-radius: 5px !important;
    }

    /* Ajuste para o Botão "Salvar/Enviar" (Grandes) */
    div[data-testid="column"] .stButton > button {
        height: 40px !important;
        width: 90% !important;
    }

    /* CSS para o Botão Atualizar (Menor e centralizado abaixo da tabela) */
    .btn-atualizar-container {
        display: flex;
        justify-content: center;
        margin-top: 10px;
    }
    .btn-atualizar-container .stButton > button {
        height: 30px !important;
        width: auto !important;
        padding: 0 20px !important;
        font-size: 12px !important;
        background-color: #34495e !important; /* Cor mais neutra para o botão de apoio */
    }

    hr { margin-top: 20px !important; margin-bottom: 5px !important; }
    .contador-estilo {
        text-align: center;
        color: #2ecc71;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 8px;
    }
    
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
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        campos = [
            ("ID:", "f_id", None), ("ALUNO:", "f_nome", None), ("CIDADE:", "f_cid", None),
            ("CURSO:", "input_curso_key", transformar_curso), ("PAGAMENTO:", "input_pagto_key", None),
            ("VENDEDOR:", "f_vend", None), ("DATA:", "f_data", None)
        ]
        for label, key, func in campos:
            c_lab, c_inp = st.columns([1.5, 3.5]) 
            c_lab.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if key == "input_curso_key":
                c_inp.text_input(label, key=key, value=st.session_state.val_curso, on_change=func, label_visibility="collapsed")
            elif key == "input_pagto_key":
                c_inp.text_input(label, key=key, value=st.session_state.val_pagto, label_visibility="collapsed")
            elif key == "f_data":
                c_inp.text_input(label, key=key, value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")
            else:
                c_inp.text_input(label, key=key, label_visibility="collapsed")

        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([0.8, 1.2, 1.2, 1.2, 0.8])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        _, b_left, b_right, _ = st.columns([0.5, 2, 2, 0.5])
        with b_left:
            if st.button("💾 SALVAR ALUNO", key="btn_salvar"):
                if st.session_state.f_nome:
                    aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), "Data": st.session_state.f_data}
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with b_right:
            if st.button("📤 ENVIAR PLANILHA", key="btn_enviar"):
                if st.session_state.lista_previa:
                    df_old = conn.read(ttl="0s").fillna(""); df_new = pd.DataFrame(st.session_state.lista_previa); conn.update(data=pd.concat([df_old, df_new], ignore_index=True)); st.session_state.lista_previa = []; st.success("Enviado!"); st.rerun()

        st.write("---") 
        qtd = len(st.session_state.lista_previa)
        st.markdown(f'<div class="contador-estilo">FILA DE ENVIO: {qtd} ALUNO(S)</div>', unsafe_allow_html=True)
        df_previa = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
        st.dataframe(df_previa, use_container_width=True, hide_index=True)

with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #2ecc71;'>🖥️ BASE DE DADOS COMPLETA</h3>", unsafe_allow_html=True)
    
    try:
        with st.spinner("Sincronizando registros..."):
            dados = conn.read(ttl="0s").fillna("")
            
            if not dados.empty:
                if "ID" in dados.columns:
                    dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
                
                # Exibição da Tabela
                st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=500)
                
                # BOTÃO ATUALIZAR (MENOR E ABAIXO DA LISTA)
                st.markdown('<div class="btn-atualizar-container">', unsafe_allow_html=True)
                if st.button("🔄 ATUALIZAR LISTA", key="btn_refresh_ger"):
                    st.cache_data.clear()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Aguardando registros ou planilha vazia.")
    except:
        st.error("Erro ao carregar os dados do Google Sheets.")

with tab_rel:
    st.markdown("<h3 style='text-align: center; color: #2ecc71;'>📊 RELATÓRIOS</h3>", unsafe_allow_html=True)
    st.info("Módulo de estatísticas em desenvolvimento.")
