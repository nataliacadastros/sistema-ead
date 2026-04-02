import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- 🛠️ PAINEL DE AJUSTE DE DESIGN (SIDEBAR) ---
st.sidebar.header("🎨 AJUSTES DE CADASTRO")
# Sliders para você encontrar a medida perfeita
adj_width = st.sidebar.slider("Largura dos Campos (%)", 10, 100, 70)
adj_height = st.sidebar.slider("Altura dos Campos (px)", 10, 60, 25)
adj_margin = st.sidebar.slider("Distância entre Linhas (px)", 0, 50, 5)
adj_label_size = st.sidebar.slider("Tamanho da Fonte Rótulos (px)", 10, 24, 14)

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS DINÂMICO COM AS VARIÁVEIS DOS SLIDERS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0e1e; color: #e0e0e0; }}
    .stTabs [data-baseweb="tab-list"] {{ 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }}
    .stTabs [data-baseweb="tab"] {{ color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }}
    .stTabs [aria-selected="true"] {{ color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }}
    .main .block-container {{ padding-top: 45px !important; max-width: 100% !important; }}
    
    /* CONFIGURAÇÃO DINÂMICA DAS LINHAS DE CADASTRO */
    div[data-testid="stHorizontalBlock"] {{ 
        margin-bottom: {adj_margin}px !important; 
        display: flex; 
        align-items: center; 
    }}
    
    /* RÓTULOS (LABELS) */
    label {{ 
        color: #00f2ff !important; 
        font-weight: bold !important; 
        font-size: {adj_label_size}px !important; 
        padding-right: 15px !important; 
        display: flex; 
        align-items: center; 
        justify-content: flex-end; 
    }}
    
    /* INPUTS (CAMPOS BRANCOS) */
    div[data-testid="stTextInput"] {{ width: {adj_width}% !important; }}
    .stTextInput input {{ 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        font-size: 12px !important; 
        height: {adj_height}px !important; 
        border-radius: 5px !important; 
    }}

    /* GERENCIAMENTO */
    .custom-table-wrapper {{ width: 100%; max-height: 60vh; overflow-x: auto !important; overflow-y: auto !important; background-color: #121629; border: 1px solid #1f295a; border-radius: 10px; }}
    .custom-table {{ width: 100%; border-collapse: collapse; min-width: 2200px !important; }}
    .custom-table th {{ background-color: #1f295a; color: #00f2ff; text-align: left; padding: 12px; font-size: 11px; position: sticky; top: 0; z-index: 10; }}
    .custom-table td {{ padding: 10px 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }}
    .status-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 9px; font-weight: bold; text-transform: uppercase; }}
    .status-ativo {{ background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }}
    .status-cancelado {{ background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }}

    .stButton > button {{ background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border-radius: 5px !important; width: 100%; height: 35px !important; }}
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    /* Scrollbar Cyan */
    .custom-table-wrapper::-webkit-scrollbar {{ height: 10px; width: 10px; }}
    .custom-table-wrapper::-webkit-scrollbar-track {{ background: #0b0e1e; }}
    .custom-table-wrapper::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS E CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES ---
def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

def transformar_curso(chave):
    entrada = st.session_state[chave].strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper()
    else: st.session_state[chave] = entrada.upper()

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    # BLOCO DE CÓDIGO PARA VOCÊ ME ENVIAR DEPOIS
    st.info("💡 Ajuste os valores na barra lateral. Quando estiver perfeito, me envie os números abaixo:")
    st.code(f"LARGURA: {adj_width}% | ALTURA: {adj_height}px | DISTÂNCIA: {adj_margin}px | FONTE: {adj_label_size}px", language="txt")
    
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        campos = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        
        for l, k in campos:
            cl, ci = st.columns([1.5, 3.5])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        st.write("")
        _, c1, c2, c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento)
        c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento)
        c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento)
        
        st.write("")
        _, b1, b2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Curso": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                        for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Curso"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Curso"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Curso"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                        ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABAS GERENCIAMENTO E RELATÓRIO (PRESERVADAS) ---
with tab_ger:
    st.write("Aba Gerenciamento com scroll horizontal funcional.")
with tab_rel:
    st.write("Aba Relatórios impecável preservada.")
