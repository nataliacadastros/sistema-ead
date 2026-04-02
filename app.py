import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS ESTÉTICA HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { 
        color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important;
        background-color: rgba(0, 242, 255, 0.05) !important;
    }
    .main .block-container { padding-top: 45px !important; max-width: 1200px !important; margin: 0 auto !important; }
    div[data-testid="stHorizontalBlock"] { margin-bottom: 5px !important; display: flex; align-items: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES DE CONTROLE ---

def atualizar_pagamento():
    # Chaves dinâmicas
    suffix_aluno = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    key_pagto = f"f_pagto_{suffix_aluno}"
    key_v_ing = f"chk_1_{suffix_aluno}"
    key_v_bon = f"chk_2_{suffix_aluno}"
    key_v_con = f"chk_3_{suffix_aluno}"

    # 1. Pegar valor atual do campo
    texto_atual = st.session_state.get(key_pagto, "")
    
    # 2. Separar o texto base (antes do primeiro "|")
    base = texto_atual.split('|')[0].strip()
    
    # 3. Criar nova string começando pela base
    novo_texto = base
    
    # 4. Verificar TODOS os checkboxes e adicionar as frases exatas
    if st.session_state.get(key_v_ing):
        novo_texto += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    
    if st.session_state.get(key_v_bon):
        novo_texto += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
        
    if st.session_state.get(key_v_con):
        novo_texto += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
        
    # 5. Atualizar o campo no session_state
    st.session_state[key_pagto] = novo_texto.upper()

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
    else: st.session_state[chave] = entrada.upper()

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        suffix_aluno = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        suffix_geral = f"g_{st.session_state.reset_geral}"

        c_id_lab, c_id_inp = st.columns([1.5, 3.5])
        c_id_lab.markdown("<label>ID:</label>", unsafe_allow_html=True)
        f_id = c_id_inp.text_input("ID", key=f"f_id_{suffix_aluno}", label_visibility="collapsed")

        c_nom_lab, c_nom_inp = st.columns([1.5, 3.5])
        c_nom_lab.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        f_nome = c_nom_inp.text_input("ALUNO", key=f"f_nome_{suffix_aluno}", label_visibility="collapsed")

        c_tr_lab, c_tr_inp = st.columns([1.5, 3.5])
        c_tr_lab.markdown("<label>TEL. RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_tel_resp = c_tr_inp.text_input("TEL. RESP", key=f"f_tel_resp_{suffix_aluno}", label_visibility="collapsed")

        c_ta_lab, c_ta_inp = st.columns([1.5, 3.5])
        c_ta_lab.markdown("<label>TEL. ALUNO:</label>", unsafe_allow_html=True)
        f_tel_aluno = c_ta_inp.text_input("TEL. ALUNO", key=f"f_tel_aluno_{suffix_aluno}", label_visibility="collapsed")

        c_cpf_lab, c_cpf_inp = st.columns([1.5, 3.5])
        c_cpf_lab.markdown("<label>CPF RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_cpf = c_cpf_inp.text_input("CPF", key=f"f_cpf_{suffix_aluno}", label_visibility="collapsed")

        c_cid_lab, c_cid_inp = st.columns([1.5, 3.5])
        c_cid_lab.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        f_cid = c_cid_inp.text_input("CIDADE", key=f"f_cid_{suffix_geral}", label_visibility="collapsed")

        c_cur_lab, c_cur_inp = st.columns([1.5, 3.5])
        c_cur_lab.markdown("<label>CURSO CONTRATADO:</label>", unsafe_allow_html=True)
        key_curso = f"input_curso_key_{suffix_aluno}"
        f_curso = c_cur_inp.text_input("CURSO", key=key_curso, on_change=transformar_curso, args=(key_curso,), label_visibility="collapsed")

        c_pag_lab, c_pag_inp = st.columns([1.5, 3.5])
        c_pag_lab.markdown("<label>FORMA DE PAGAMENTO:</label>", unsafe_allow_html=True)
        f_pagto = c_pag_inp.text_input("PAGAMENTO", key=f"f_pagto_{suffix_aluno}", label_visibility="collapsed")

        c_ven_lab, c_ven_inp = st.columns([1.5, 3.5])
        c_ven_lab.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        f_vend = c_ven_inp.text_input("VENDEDOR", key=f"f_vend_{suffix_geral}", label_visibility="collapsed")

        c_dat_lab, c_dat_inp = st.columns([1.5, 3.5])
        c_dat_lab.markdown("<label>DATA DA MATRÍCULA:</label>", unsafe_allow_html=True)
        f_data = c_dat_inp.text_input("DATA", key=f"f_data_{suffix_geral}", label_visibility="collapsed")

        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        c_c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{suffix_aluno}", on_change=atualizar_pagamento)
        c_c2.checkbox("CURSO BÔNUS", key=f"chk_2_{suffix_aluno}", on_change=atualizar_pagamento)
        c_c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{suffix_aluno}", on_change=atualizar_pagamento)

        st.write("")
        _, b_col1, b_col2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        
        with b_col1:
            if st.button("💾 SALVAR ALUNO"):
                if f_nome:
                    aluno = {
                        "ID": f_id.upper(), "Aluno": f_nome.upper(), "Tel_Resp": f_tel_resp,
                        "Tel_Aluno": f_tel_aluno, "CPF": f_cpf, "Cidade": f_cid.upper(),
                        "Curso": f_curso.upper(), "Pagto": f_pagto.upper(),
                        "Vendedor": f_vend.upper(), "Data_Mat": f_data
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.reset_aluno += 1
                    st.rerun()

        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        credentials = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
                        client = gspread.authorize(credentials)
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        worksheet = sh.get_worksheet(0)

                        dados_finais = []
                        hoje = date.today().strftime("%d/%m/%Y")
                        for a in st.session_state.lista_previa:
                            col_d = "SIM" if "10 CURSOS PROFISSIONALIZANTES" in a["Curso"].upper() else "NÃO"
                            col_e = "A DEFINIR" if "INGLÊS" in a["Curso"].upper() else "NÃO"
                            linha = ["ATIVO", "MGA", "A DEFINIR", col_d, col_e, hoje, 
                                     a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], 
                                     a["Cidade"], a["Curso"], a["Pagto"], a["Vendedor"], a["Data_Mat"]]
                            dados_finais.append(linha)

                        col_a = worksheet.col_values(1)
                        linha_ini = len(col_a) + 2 if len(col_a) > 0 else 2
                        worksheet.insert_rows(dados_finais, row=linha_ini)
                        
                        st.session_state.lista_previa = []
                        st.session_state.reset_geral += 1
                        st.success("Enviado com sucesso!")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

        st.write("---")
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #00f2ff;'>🖥️ DATABASE MONITOR</h3>", unsafe_allow_html=True)
    try:
        dados_raw = conn.read(ttl="0s").fillna("")
        st.dataframe(dados_raw.iloc[::-1], use_container_width=True, hide_index=True, height=500)
    except: st.error("Erro na conexão.")
