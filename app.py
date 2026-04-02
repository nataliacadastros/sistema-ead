import streamlit as st
import pandas as pd
import re
from datetime import date, datetime
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
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 13px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 28px !important; border-radius: 5px !important; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""

# --- FUNÇÕES AUXILIARES ---
def transformar_curso():
    entrada = st.session_state.input_curso_key.strip()
    if not entrada: st.session_state.val_curso = ""; return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state.val_curso = f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)
        else: st.session_state.val_curso = entrada.upper()
    else: st.session_state.val_curso = entrada.upper()
    st.session_state.val_curso = st.session_state.val_curso.upper().strip()
    st.session_state.input_curso_key = st.session_state.val_curso

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        # Ordem solicitada dos campos
        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>ID:</label>", unsafe_allow_html=True)
        f_id = col2.text_input("ID", key="f_id", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        f_nome = col2.text_input("ALUNO", key="f_nome", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>TEL. RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_tel_resp = col2.text_input("TEL. RESPONSÁVEL", key="f_tel_resp", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>TEL. ALUNO:</label>", unsafe_allow_html=True)
        f_tel_aluno = col2.text_input("TEL. ALUNO", key="f_tel_aluno", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>CPF RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_cpf = col2.text_input("CPF RESPONSÁVEL", key="f_cpf", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        f_cid = col2.text_input("CIDADE", key="f_cid", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>CURSO CONTRATADO:</label>", unsafe_allow_html=True)
        f_curso = col2.text_input("CURSO", key="input_curso_key", on_change=transformar_curso, label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>FORMA DE PAGAMENTO:</label>", unsafe_allow_html=True)
        f_pagto = col2.text_input("PAGAMENTO", key="f_pagto", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        f_vend = col2.text_input("VENDEDOR", key="f_vend", label_visibility="collapsed")

        col1, col2 = st.columns([1.5, 3.5])
        col1.markdown("<label>DATA DA MATRÍCULA:</label>", unsafe_allow_html=True)
        # Mantém a data padrão se não houver valor
        if "f_data" not in st.session_state: st.session_state.f_data = date.today().strftime("%d/%m/%Y")
        f_data = col2.text_input("DATA", key="f_data", label_visibility="collapsed")

        st.write("")
        b1, b2 = st.columns(2)
        
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if f_nome:
                    novo_aluno = {
                        "ID": f_id.upper(), "Aluno": f_nome.upper(), "Tel_Resp": f_tel_resp,
                        "Tel_Aluno": f_tel_aluno, "CPF": f_cpf, "Cidade": f_cid.upper(),
                        "Curso": st.session_state.val_curso if st.session_state.val_curso else f_curso.upper(),
                        "Pagto": f_pagto.upper(), "Vendedor": f_vend.upper(), "Data_Mat": f_data
                    }
                    st.session_state.lista_previa.append(novo_aluno)
                    
                    # LIMPEZA CONFORME REGRA ANTERIOR: Mantém Cidade, Vendedor e Data Matrícula
                    st.session_state.f_id = ""
                    st.session_state.f_nome = ""
                    st.session_state.f_tel_resp = ""
                    st.session_state.f_tel_aluno = ""
                    st.session_state.f_cpf = ""
                    st.session_state.input_curso_key = ""
                    st.session_state.val_curso = ""
                    st.session_state.f_pagto = ""
                    st.rerun()

        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
                        client = gspread.authorize(credentials)
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        worksheet = sh.get_worksheet(0)

                        dados_finais = []
                        data_hoje = date.today().strftime("%d/%m/%Y")

                        for a in st.session_state.lista_previa:
                            # Lógica Coluna D (SIM se 10 CURSOS PROFISSIONALIZANTES)
                            col_d = "SIM" if "10 CURSOS PROFISSIONALIZANTES" in a["Curso"] else "NÃO"
                            
                            # Lógica Coluna E (INGLÊS)
                            col_e = "A DEFINIR" if "INGLÊS" in a["Curso"] else "NÃO"

                            linha = [
                                "ATIVO",           # A
                                "MGA",             # B
                                "A DEFINIR",       # C (TURMA - Gerenciamento em lote)
                                col_d,             # D
                                col_e,             # E (INGLÊS? - Gerenciamento em lote)
                                data_hoje,         # F (Data Cadastro)
                                a["ID"],           # G
                                a["Aluno"],        # H
                                a["Tel_Resp"],     # I
                                a["Tel_Aluno"],    # J
                                a["CPF"],          # K
                                a["Cidade"],       # L
                                a["Curso"],        # M
                                a["Pagto"],        # N
                                a["Vendedor"],     # O
                                a["Data_Mat"]      # P
                            ]
                            dados_finais.append(linha)

                        col_a_values = worksheet.col_values(1)
                        ultima_linha = len(col_a_values)
                        linha_inicio = ultima_linha + 2 if ultima_linha > 0 else 2
                        
                        worksheet.insert_rows(dados_finais, row=linha_inicio)
                        
                        # Limpa tudo após enviar para a planilha
                        st.session_state.lista_previa = []
                        st.session_state.f_cid = ""
                        st.session_state.f_vend = ""
                        st.success("Dados enviados com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")

        st.write("---")
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #00f2ff;'>🖥️ DATABASE MONITOR & BATCH EDIT</h3>", unsafe_allow_html=True)
    try:
        dados_brutos = conn.read(ttl="0s").fillna("")
        if not dados_brutos.empty:
            # Seleção para alteração em lote (Exemplo de interface)
            st.write("Selecione os alunos abaixo para alterar Turma (Col C) ou Inglês (Col E):")
            
            # Dataframe Interativo para seleção
            selected_rows = st.dataframe(
                dados_brutos.iloc[::-1], 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row"
            )
            
            # Bloco de edição em lote
            if selected_rows.selection.rows:
                st.info(f"{len(selected_rows.selection.rows)} alunos selecionados.")
                c_edit1, c_edit2 = st.columns(2)
                nova_turma = c_edit1.text_input("Nova Turma (Coluna C)")
                nova_turma_ing = c_edit2.text_input("Nova Turma Inglês (Coluna E)")
                
                if st.button("Confirmar Alteração em Lote"):
                    st.warning("Implementando conexão direta para update de células específicas via Gspread...")
                    # Aqui entra a lógica de worksheet.update_cell para as linhas selecionadas
            
            if st.button("🔄 REFRESH"): st.cache_data.clear(); st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")

with tab_rel:
    st.info("Aba de relatórios mantida para análise de desempenho.")
