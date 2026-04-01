import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CSS INTEGRADO (CADASTRO ESCURO + GERENCIAMENTO CRM) ---
st.markdown("""
    <style>
    /* Estilo Base */
    .stApp { background-color: #f0f2f6; }
    .block-container { padding-top: 0rem !important; max-width: 100% !important; }

    /* MENU SUPERIOR (TABS) - ESTILO CRM AZUL */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px; background-color: #1a3a5a; padding: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px; color: #ffffff !important; font-weight: 500;
        border: none; background-color: transparent; padding: 0px 30px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c5282 !important; border-bottom: 3px solid #63b3ed !important;
    }

    /* --- ESTILO ESPECÍFICO DO CADASTRO (RESTAURADO) --- */
    .cadastro-container {
        background-color: #1a2436; 
        padding: 20px; 
        border-radius: 0px; 
        color: white;
        min-height: 100vh;
    }
    
    /* Inputs Compactos no Cadastro */
    div[data-testid="stTextInput"] > div { min-height: 24px !important; height: 24px !important; }
    .stTextInput input { 
        background-color: white !important; color: black !important; 
        height: 24px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 12px !important; padding: 0px 8px !important;
    }
    
    /* Labels Verdes Laterais */
    .cad-label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 12px !important; 
        display: flex; align-items: center; height: 24px; justify-content: flex-end; padding-right: 15px;
    }
    
    /* Botões Verdes do Cadastro */
    .btn-cad div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 35px !important; width: 100% !important;
        border: none !important;
    }

    /* Checkboxes Cadastro */
    .stCheckbox label p { font-size: 11px !important; color: #2ecc71 !important; font-weight: bold; }

    /* --- ESTILO GERENCIAMENTO --- */
    .stDataFrame { background-color: white !important; border: 1px solid #e6e9ef; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL (VOLTANDO AO PADRÃO ANTERIOR) ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 2.5]) 
    with c1: st.markdown(f"<div class='cad-label'>{label}</div>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# ================= ABA 1: CADASTRO (RESTAURADA) =================
with abas[0]:
    # Aplicando fundo escuro apenas nesta aba
    st.markdown('<div class="cadastro-container">', unsafe_allow_html=True)
    
    _, col_form, _ = st.columns([1, 1.8, 1])
    with col_form:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado)
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        st.write("")
        # Checkboxes agrupados
        c_sel = st.columns([1, 1, 1.2])
        with c_sel[0]: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c_sel[1]: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c_sel[2]: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        st.write("")
        # Botões de ação
        st.markdown('<div class="btn-cad">', unsafe_allow_html=True)
        c_btns = st.columns(2)
        with c_btns[0]:
            if st.button("SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_field.upper(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with c_btns[1]:
            if st.button("FINALIZAR PDF"):
                if st.session_state.lista_previa:
                    df_sheets = conn.read(ttl="0s").fillna("")
                    df_novos = pd.DataFrame(st.session_state.lista_previa)
                    df_final = pd.concat([df_sheets, df_novos], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    # Tabela branca de prévia
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=200)
    st.markdown('</div>', unsafe_allow_html=True)

# ================= ABA 2: GERENCIAMENTO (ESTILO CRM) =================
with abas[1]:
    st.write("")
    # Barra de Ferramentas Estilo CRM
    t1, t2, t3 = st.columns([3, 1, 1])
    with t1:
        busca = st.text_input("", placeholder="🔍 Filtrar base de dados...", label_visibility="collapsed").upper()
    with t2:
        if st.button("🔄 Sincronizar Base"):
            st.rerun()
    with t3:
        st.button("➕ Novo Registro", disabled=True)

    try:
        dados_reais = conn.read(ttl="0s").fillna("")
        if busca:
            mask = dados_reais.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_reais = dados_reais[mask]

        st.dataframe(dados_reais, use_container_width=True, hide_index=True, height=600)
    except:
        st.error("Erro ao carregar a planilha.")

# ================= ABA 3: RELATÓRIOS =================
with abas[2]:
    st.write("Estatísticas e gráficos.")
