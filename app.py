import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA TELA DE CADASTRO TÉCNICA E GERENCIAMENTO LIMPO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0rem !important; max-width: 100% !important; }

    /* MENU SUPERIOR */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: #0d1626; padding: 5px 20px;
        border-bottom: 2px solid #004a99;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px; color: white !important; font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2ecc71 !important; border-radius: 4px;
    }

    /* ESTILO DOS INPUTS (IGUAL ANTES) */
    div[data-testid="stTextInput"] > div { min-height: 24px !important; height: 24px !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 24px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 12px !important; padding: 0px 8px !important;
    }
    
    /* LABELS LATERAIS */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 12px !important; 
        display: flex; align-items: center; height: 24px; justify-content: flex-end; padding-right: 15px;
    }
    
    /* BOTÕES VERDES */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 35px !important; width: 100% !important;
    }

    /* CHECKBOXES COLADOS */
    .stCheckbox label p { font-size: 11px !important; color: #2ecc71 !important; font-weight: bold; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO HORIZONTAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 2.5]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# ================= ABA 1: CADASTRO (IGUAL ANTES) =================
with abas[0]:
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
        c_sel = st.columns([1, 1, 1.2])
        with c_sel[0]: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c_sel[1]: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c_sel[2]: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        st.write("")
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

    st.write("")
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=200)

# ================= ABA 2: GERENCIAMENTO (PUXANDO PLANILHA) =================
with abas[1]:
    st.write("### 🖥️ Controle Geral de Matrículas")
    
    # Botão de atualizar base
    if st.button("🔄 Sincronizar com Google Sheets"):
        st.cache_data.clear()
        st.rerun()

    try:
        # Puxa os dados reais da planilha
        dados_reais = conn.read(ttl="0s").fillna("")
        
        # Campo de busca para o gerenciamento
        busca = st.text_input("🔍 Pesquisar na planilha (Aluno, Vendedor, Cidade...):").upper()
        
        if busca:
            mask = dados_reais.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_reais = dados_reais[mask]

        # Exibe a planilha bruta de forma profissional
        st.dataframe(dados_reais, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error("Não foi possível carregar os dados. Verifique se a URL da planilha está correta no Secrets.")

# ================= ABA 3: RELATÓRIOS =================
with abas[2]:
    st.write("### 📊 Relatórios e Indicadores")
    st.info("Esta aba será destinada a gráficos e estatísticas futuras.")
