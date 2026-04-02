import streamlit as st
import pandas as pd
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

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a3a5a; border-bottom: 2px solid #2c5282; }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; font-weight: 600; padding: 0px 30px; }
    .stTabs [aria-selected="true"] { background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; display: flex; align-items: center; justify-content: flex-end; padding-right: 15px; height: 25px; }
    div.stButton > button { background-color: #2ecc71 !important; color: white !important; font-weight: bold !important; height: 40px !important; width: 100% !important; border: none !important; }
    .stDataFrame { background-color: white !important; color: black !important; border-radius: 4px; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# --- LÓGICA DO CAMPO CURSO (SUBSTITUIÇÃO CORRIGIDA) ---
def transformar_curso():
    # Pega o conteúdo atual do widget
    conteudo_input = st.session_state.input_curso_key.strip()
    
    if conteudo_input:
        # 1. Tenta quebrar por "+" para ver se o usuário digitou um novo código após um curso já existente
        partes = [p.strip() for p in conteudo_input.split('+')]
        
        # 2. O que nos interessa é o que foi digitado por último
        ultimo_termo = partes[-1].upper()
        
        # 3. Verifica se esse último termo é um código numérico do dicionário
        if ultimo_termo in DIC_CURSOS:
            nome_curso = DIC_CURSOS[ultimo_termo]
            
            # Substitui o código pelo nome
            partes[-1] = nome_curso
            
            # Remove duplicatas mantendo a ordem
            resultado = []
            for item in partes:
                if item.upper() not in [r.upper() for r in resultado]:
                    resultado.append(item.upper())
            
            # Reconstrói a string com o " + " e o espaço no final
            st.session_state.val_curso = " + ".join(resultado) + " "
        else:
            # Se o usuário digitou algo que não é código, apenas padroniza
            st.session_state.val_curso = conteudo_input.upper() + " "
    
    # Sincroniza o widget com o valor processado
    st.session_state.input_curso_key = st.session_state.val_curso

# --- LÓGICA DO PAGAMENTO ---
def processar_pagto():
    base = st.session_state.input_pagto_key.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_1: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if st.session_state.chk_3: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    
    final = base
    if obs: final += " | " + " | ".join(obs)
    
    st.session_state.val_pagto = final
    st.session_state.input_pagto_key = final

# --- UI ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, col, _ = st.columns([0.5, 3, 0.5])
    with col:
        st.write("")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ID:</label>", unsafe_allow_html=True); f_id = c2.text_input("ID", key="f_id", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ALUNO:</label>", unsafe_allow_html=True); f_nome = c2.text_input("ALUNO", key="f_nome", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CIDADE:</label>", unsafe_allow_html=True); f_cid = c2.text_input("CIDADE", key="f_cid", label_visibility="collapsed")
        
        # Campo CURSO
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        c2.text_input("CURSO", key="input_curso_key", value=st.session_state.val_curso, on_change=transformar_curso, label_visibility="collapsed")
        
        # Campo PAGAMENTO
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        c2.text_input("PAGAMENTO", key="input_pagto_key", value=st.session_state.val_pagto, label_visibility="collapsed")
        
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True); f_vend = c2.text_input("VENDEDOR", key="f_vend", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>DATA:</label>", unsafe_allow_html=True); f_data = c2.text_input("DATA", key="f_data", value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")

        st.write("")
        s1, s2, s3 = st.columns(3)
        with s1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with s2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with s3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.f_nome:
                    aluno = {
                        "ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(),
                        "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(),
                        "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(),
                        "Data": st.session_state.f_data
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.val_curso = ""; st.session_state.val_pagto = ""
                    st.session_state.f_nome = ""; st.session_state.f_id = ""
                    st.rerun()
        with b2:
            if st.button("📤 ENVIAR PARA PLANILHA"):
                if st.session_state.lista_previa:
                    df_old = conn.read(ttl="0s").fillna("")
                    df_new = pd.DataFrame(st.session_state.lista_previa)
                    conn.update(data=pd.concat([df_old, df_new], ignore_index=True))
                    st.session_state.lista_previa = []
                    st.success("Enviado com sucesso!")
                    st.rerun()

    st.write("---")
    if st.session_state.lista_previa:
        st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

with tab_ger:
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns:
            dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=600)
    except:
        st.error("Erro ao carregar banco de dados.")
