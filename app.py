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

# --- CSS DEFINITIVO (ESTILO TÉCNICO) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a3a5a; border-bottom: 2px solid #2c5282; }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; font-weight: 600; padding: 0px 30px; }
    .stTabs [aria-selected="true"] { background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important; }
    
    /* Campos de Texto */
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    .stTextInput input { 
        background-color: white !important; color: black !important; 
        text-transform: uppercase !important; font-size: 12px !important; 
    }
    
    /* Labels Verdes Alinhadas */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; justify-content: flex-end; padding-right: 15px; height: 25px;
    }
    
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important; font-weight: bold !important;
        height: 40px !important; width: 100% !important; border: none !important;
    }
    
    .stDataFrame { background-color: white !important; color: black !important; border-radius: 4px; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E INICIALIZAÇÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicializa todos os estados necessários
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "txt_curso" not in st.session_state: st.session_state.txt_curso = ""
if "txt_pagto" not in st.session_state: st.session_state.txt_pagto = ""

# --- LÓGICA DE PROCESSAMENTO DO CURSO ---
def processar_curso():
    entrada = st.session_state.input_curso_widget.strip()
    if entrada:
        # Pega a última parte após o "+" ou o texto todo
        partes = [p.strip() for p in entrada.split('+')]
        ultimo = partes[-1]
        
        if ultimo in DIC_CURSOS:
            partes[-1] = DIC_CURSOS[ultimo]
            st.session_state.txt_curso = (" + ".join(partes)).upper() + " "
        else:
            st.session_state.txt_curso = entrada.upper() + " "
    # Sincroniza o widget com o texto processado
    st.session_state.input_curso_widget = st.session_state.txt_curso

# --- LÓGICA DE PAGAMENTO (CHECKBOXES) ---
def atualizar_pagto():
    base = st.session_state.input_pagto_widget.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_lib: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_bonus: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if st.session_state.chk_conf: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    
    if obs:
        st.session_state.txt_pagto = f"{base} | {' | '.join(obs)}"
    else:
        st.session_state.txt_pagto = base
    st.session_state.input_pagto_widget = st.session_state.txt_pagto

# --- INTERFACE ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with abas[0]:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    with col_central:
        st.write("")
        # Linhas do Formulário
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ID:</label>", unsafe_allow_html=True); id_val = c2.text_input("ID", key="id_k", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>ALUNO:</label>", unsafe_allow_html=True); nome_val = c2.text_input("ALUNO", key="nome_k", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CIDADE:</label>", unsafe_allow_html=True); cid_val = c2.text_input("CIDADE", key="cid_k", label_visibility="collapsed")
        
        # CAMPO CURSO (SUBSTITUIÇÃO AO DAR ENTER)
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        c2.text_input("CURSO", key="input_curso_widget", value=st.session_state.txt_curso, on_change=processar_curso, label_visibility="collapsed")
        
        # CAMPO PAGAMENTO
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        c2.text_input("PAGAMENTO", key="input_pagto_widget", value=st.session_state.txt_pagto, label_visibility="collapsed")
        
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True); vend_val = c2.text_input("VENDEDOR", key="vend_k", label_visibility="collapsed")
        c1, c2 = st.columns([1.2, 4]); c1.markdown("<label>DATA:</label>", unsafe_allow_html=True); data_val = c2.text_input("DATA", key="data_k", value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")

        # CHECKBOXES (BOTÕES SELECIONÁVEIS)
        st.write("")
        s1, s2, s3 = st.columns(3)
        with s1: st.checkbox("LIB. IN-GLÊS", key="chk_lib", on_change=atualizar_pagto)
        with s2: st.checkbox("CURSO BÔNUS", key="chk_bonus", on_change=atualizar_pagto)
        with s3: st.checkbox("CONFIRMAÇÃO", key="chk_conf", on_change=atualizar_pagto)

        # BOTÕES DE SALVAR
        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_k:
                    novo_aluno = {
                        "ID": st.session_state.id_k, "Aluno": st.session_state.nome_k.upper(),
                        "Cidade": st.session_state.cid_k.upper(), "Curso": st.session_state.input_curso_widget.strip(),
                        "Pagamento": st.session_state.input_pagto_widget.upper(), "Vendedor": st.session_state.vend_k.upper(),
                        "Data": st.session_state.data_k
                    }
                    st.session_state.lista_previa.append(novo_aluno)
                    # Reset Campos
                    st.session_state.txt_curso = ""; st.session_state.txt_pagto = ""
                    st.session_state.nome_k = ""; st.session_state.id_k = ""
                    st.rerun()
        with b2:
            if st.button("📤 ENVIAR TUDO"):
                if st.session_state.lista_previa:
                    df_planilha = conn.read(ttl="0s").fillna("")
                    df_novos = pd.DataFrame(st.session_state.lista_previa)
                    df_final = pd.concat([df_planilha, df_novos], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.success("Enviado!")
                    st.rerun()

    # LISTA DE PRÉ-VISUALIZAÇÃO CORRIGIDA
    st.write("### Pré-visualização (Aguardando Envio)")
    df_previa = pd.DataFrame(st.session_state.lista_previa)
    if not df_previa.empty:
        st.dataframe(df_previa, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum aluno na lista de espera.")

with abas[1]:
    # GERENCIAMENTO CRM
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns:
            dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=600)
    except:
        st.error("Erro ao carregar banco de dados.")
