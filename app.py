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

# --- CSS ESTÉTICA HUD NEON & GERENCIAMENTO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
    .main .block-container { padding-top: 45px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    /* ESTILO CADASTRO (FIXO) */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 55% !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }

    /* GERENCIAMENTO */
    .custom-table-wrapper { width: 100%; max-height: 650px; overflow: auto !important; background-color: #121629; border: 1px solid #1f295a; border-radius: 10px; padding: 10px; }
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* BOTÃO ID ESTILIZADO */
    .stButton > button[key^="id_btn_"] {
        background-color: transparent !important;
        color: #00f2ff !important;
        border: 1px solid #1f295a !important;
        font-weight: bold !important;
        width: 100% !important;
        text-decoration: underline;
    }
    .stButton > button[key^="id_btn_"]:hover {
        background-color: rgba(0, 242, 255, 0.1) !important;
        border-color: #00f2ff !important;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES ---
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

@st.dialog("📝 ALTERAR DADOS DO ALUNO")
def editar_aluno_dialog(dados_atuais):
    st.markdown(f"Alterando registro de: **{dados_atuais['ALUNO']}**")
    cols = st.columns(2)
    novos_dados = {}
    ordem_colunas = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
    
    for i, col in enumerate(ordem_colunas):
        with cols[i % 2]:
            novos_dados[col] = st.text_input(col, value=str(dados_atuais.get(col, "")))

    st.write("---")
    if st.button("✅ SALVAR ALTERAÇÕES NA PLANILHA", use_container_width=True):
        try:
            creds = st.secrets["connections"]["gsheets"]
            client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
            ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
            
            cell = ws.find(str(dados_atuais['ID']), in_column=7)
            if cell:
                lista_atualizada = [novos_dados[c] for c in ordem_colunas]
                ws.update(range_name=f"A{cell.row}:P{cell.row}", values=[lista_atualizada])
                st.success("Sincronizado com sucesso!")
                st.cache_data.clear()
                st.rerun()
            else: st.error("ID não localizado na planilha.")
        except Exception as e: st.error(f"Erro: {e}")

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
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
        _, b1, b2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "ALUNO": st.session_state[f"f_nome_{s_al}"].upper(), "TEL_RESP": st.session_state[f"f_tel_resp_{s_al}"], "TEL_ALU": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "CIDADE": st.session_state[f"f_cid_{s_ge}"].upper(), "CURSO": st.session_state[f"input_curso_key_{s_al}"].upper(), "PAGTO": st.session_state[f"f_pagto_{s_al}"].upper(), "VEND.": st.session_state[f"f_vend_{s_ge}"].upper(), "DT_MAT": st.session_state[f"f_data_{s_ge}"]})
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                    for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["CURSO"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["CURSO"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["ALUNO"], a["TEL_RESP"], a["TEL_ALU"], a["CPF"], a["CIDADE"], a["CURSO"], a["PAGTO"], a["VEND."], a["DT_MAT"]])
                    ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                    st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.cache_data.clear(); st.rerun()

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    cf1, cf2, cf3 = st.columns([3, 1, 1])
    with cf1: bu = st.text_input("🔍 Filtrar na Lista...", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf3: 
        if st.button("🔄 ATUALIZAR"): st.cache_data.clear(); st.rerun()

    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].astype(str).str.contains(bu)]

        # Cabeçalho da Tabela
        st.markdown(f"""
            <table style='width:2500px; border-collapse:collapse; background:#1f295a; color:#00f2ff; font-size:11px;'>
            <tr>
                <th style='width:100px; padding:12px;'>STATUS</th>
                <th style='width:120px;'>ID (CLIQUE)</th>
                <th style='width:300px;'>ALUNO</th>
                <th style='width:150px;'>TURMA</th>
                <th style='width:250px;'>CURSO</th>
                <th style='width:200px;'>PAGAMENTO</th>
                <th style='width:150px;'>CIDADE</th>
                <th style='width:150px;'>VENDEDOR</th>
                <th style='width:120px;'>DATA MAT.</th>
            </tr></table>
        """, unsafe_allow_html=True)

        st.markdown("<div class='custom-table-wrapper'>", unsafe_allow_html=True)
        for index, row in df_g.iloc[::-1].iterrows():
            c_id, c_rest = st.columns([0.08, 0.92])
            
            # O ID agora é um botão que dispara o dialog
            if c_id.button(str(row['ID']), key=f"id_btn_{row['ID']}_{index}"):
                editar_aluno_dialog(row.to_dict())
            
            sc = "status-ativo" if row['STATUS'] == "ATIVO" else "status-cancelado"
            c_rest.markdown(f"""
                <table style='width:2380px; border-collapse:collapse; background:#121629; font-size:11px;'>
                <tr style='border-bottom:1px solid #1f295a;'>
                    <td style='width:100px; padding:10px;'><span class='status-badge {sc}'>{row['STATUS']}</span></td>
                    <td style='width:300px; color:#e0e0e0; font-weight:bold;'>{row['ALUNO']}</td>
                    <td style='width:150px;'>{row['TURMA']}</td>
                    <td style='width:250px;'>{row['CURSO']}</td>
                    <td style='width:200px;'>{row['PAGTO']}</td>
                    <td style='width:150px;'>{row['CIDADE']}</td>
                    <td style='width:150px;'>{row['VEND.']}</td>
                    <td style='width:120px;'>{row['DT_MAT']}</td>
                </tr></table>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro ao carregar dados: {e}")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    st.info("Aba Relatórios preservada.")
