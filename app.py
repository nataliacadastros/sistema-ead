import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
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
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { 
        color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important;
        background-color: rgba(0, 242, 255, 0.05) !important;
    }
    .main .block-container { padding-top: 45px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    /* ESTILO CADASTRO */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 55% !important; }
    .stTextInput input { 
        background-color: white !important; color: black !important; text-transform: uppercase !important; 
        font-size: 12px !important; height: 18px !important; border-radius: 5px !important; 
    }

    /* ESTILO DO BOTÃO DE ID (PARA PARECER TEXTO) */
    button[key^="btn_edit_"] {
        background: none !important;
        border: none !important;
        padding: 0 !important;
        color: #00f2ff !important;
        font-weight: bold !important;
        text-align: left !important;
        font-size: 11px !important;
        cursor: pointer !important;
    }

    /* GERENCIAMENTO - CONTAINER */
    .custom-table-wrapper {
        width: 100%;
        max-height: 600px; 
        overflow-x: auto !important; 
        overflow-y: auto !important;
        background-color: #121629;
        border: 2px solid #1f295a;
        border-radius: 10px;
        margin-top: 15px;
        padding: 10px;
    }

    .stButton > button { background-color: #00f2ff; color: #0b0e1e; font-weight: bold; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÃO DE EDIÇÃO (FRAME) ---
@st.dialog("📋 ALTERAR DADOS DO ALUNO")
def abrir_frame_edicao(dados_aluno):
    st.write(f"Editando Registro de: **{dados_aluno['ALUNO']}**")
    col_a, col_b = st.columns(2)
    novos_dados = {}
    campos = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
    
    for i, campo in enumerate(campos):
        with col_a if i % 2 == 0 else col_b:
            novos_dados[campo] = st.text_input(campo, value=str(dados_aluno.get(campo, "")))
    
    st.write("---")
    if st.button("✅ SALVAR ALTERAÇÕES"):
        try:
            creds = st.secrets["connections"]["gsheets"]
            client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
            ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
            cell = ws.find(str(dados_aluno['ID']), in_column=7)
            if cell:
                linha_atualizada = [novos_dados[c] for c in campos]
                ws.update(range_name=f"A{cell.row}:P{cell.row}", values=[linha_atualizada])
                st.success("Alterado com sucesso!")
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- FUNÇÕES DE CONTROLE ---
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

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        c = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
             ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
             ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
             ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in c:
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
                    st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                        for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                        ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    with cf4: 
        if st.button("🔄", key="btn_refresh"): st.cache_data.clear(); st.rerun()

    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        if bu: df_g = df_g[df_g['ALUNO'].astype(str).str.contains(bu, case=False) | df_g['ID'].astype(str).str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]

        # Cabeçalho Fixo
        st.markdown(f"""
            <div style="background-color: #1f295a; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                <table style="width: 2500px; border-collapse: collapse; table-layout: fixed;">
                    <tr style="color: #00f2ff; font-size: 11px; text-transform: uppercase; font-weight: bold;">
                        <td style="width: 120px;">STATUS</td><td style="width: 100px;">UNID.</td><td style="width: 120px;">TURMA</td>
                        <td style="width: 80px;">10C</td><td style="width: 80px;">ING</td><td style="width: 120px;">DT_CAD</td>
                        <td style="width: 100px;">ID</td><td style="width: 250px;">ALUNO</td><td style="width: 150px;">TEL_RESP</td>
                        <td style="width: 150px;">TEL_ALU</td><td style="width: 150px;">CPF</td><td style="width: 150px;">CIDADE</td>
                        <td style="width: 250px;">CURSO</td><td style="width: 300px;">PAGTO</td><td style="width: 150px;">VEND.</td>
                        <td style="width: 120px;">DT_MAT</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="custom-table-wrapper">', unsafe_allow_html=True)
        for idx, r in df_g.iloc[::-1].iterrows():
            sc = "status-badge status-ativo" if r['STATUS'] == "ATIVO" else "status-badge status-cancelado"
            
            # Linha de dados usando colunas Streamlit para garantir o clique
            c = st.columns([120, 100, 120, 80, 80, 120, 100, 250, 150, 150, 150, 150, 250, 300, 150, 120])
            
            with c[0]: st.markdown(f'<span class="{sc}">{r["STATUS"]}</span>', unsafe_allow_html=True)
            with c[1]: st.write(f"<small>{r['UNID.']}</small>", unsafe_allow_html=True)
            with c[2]: st.write(f"<small>{r['TURMA']}</small>", unsafe_allow_html=True)
            with c[3]: st.write(f"<small>{r['10C']}</small>", unsafe_allow_html=True)
            with c[4]: st.write(f"<small>{r['ING']}</small>", unsafe_allow_html=True)
            with c[5]: st.write(f"<small>{r['DT_CAD']}</small>", unsafe_allow_html=True)
            with c[6]: 
                if st.button(str(r['ID']), key=f"btn_edit_{r['ID']}_{idx}"):
                    abrir_frame_edicao(r.to_dict())
            with c[7]: st.markdown(f"<small><b>{r['ALUNO']}</b></small>", unsafe_allow_html=True)
            with c[8]: st.write(f"<small>{r['TEL_RESP']}</small>", unsafe_allow_html=True)
            with c[9]: st.write(f"<small>{r['TEL_ALU']}</small>", unsafe_allow_html=True)
            with c[10]: st.write(f"<small>{r['CPF']}</small>", unsafe_allow_html=True)
            with c[11]: st.write(f"<small>{r['CIDADE']}</small>", unsafe_allow_html=True)
            with c[12]: st.write(f"<small>{r['CURSO']}</small>", unsafe_allow_html=True)
            with c[13]: st.write(f"<small>{r['PAGTO']}</small>", unsafe_allow_html=True)
            with c[14]: st.write(f"<small>{r['VEND.']}</small>", unsafe_allow_html=True)
            with c[15]: st.write(f"<small>{r['DT_MAT']}</small>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 5px 0; border-color: #1f295a;'>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# Aba Relatórios omitida para brevidade (mantida igual ao seu original)
