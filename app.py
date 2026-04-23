import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO

# --- DEFINIÇÃO DO CAMINHO DA LOGO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- ARQUIVOS E PERSISTÊNCIA ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict) and "tags" in conteudo:
                    return conteudo
                elif isinstance(conteudo, dict):
                    return {"tags": conteudo, "last_selection": {}}
        except: 
            return padrao
    return padrao

def salvar_tags(dados):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    
    /* REMOVE BARREIRAS LATERAIS DO STREAMLIT GLOBALMENTE */
    [data-testid="stAppViewBlockContainer"] { 
        padding-top: 40px !important; 
        padding-left: 0px !important; 
        padding-right: 0px !important; 
        max-width: 100% !important; 
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 100% !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; transition: all 0.3s ease !important; }
    div.stButton > button:hover { background-color: #00d4df !important; box-shadow: 0 0 15px rgba(0, 242, 255, 0.6) !important; color: #000000 !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
    
    .logo-container {
        position: relative;
        top: -10px;
        left: 0px;
        margin-bottom: 10px;
    }

    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        return conn.read(ttl="10s").dropna(how='all')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES AUXILIARES ---
def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None

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

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave])
    if len(valor) == 11:
        st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    if os.path.exists(caminho_logo):
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image(caminho_logo, width=90)
        st.markdown('</div>', unsafe_allow_html=True)
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        st.write("")
        _, b1, b2, _ = st.columns([1.2, 1.9, 1.9, 0.2])
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({
                        "ID": st.session_state[f"f_id_{s_al}"].upper(),
                        "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                        "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]),
                        "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]),
                        "CPF": st.session_state[f"f_cpf_{s_al}"],
                        "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(),
                        "Course": st.session_state[f"input_curso_key_{s_al}"].upper(),
                        "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(),
                        "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(),
                        "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                    })
                    st.session_state.reset_aluno += 1
                    st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    st.success("Simulação: Alunos enviados com sucesso!")
                    st.session_state.lista_previa = []
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    # --- PAINEL DE CONTROLE MANUAL ---
    with st.expander("🛠️ AJUSTAR DIMENSÕES DA TABELA (CONTROLE MANUAL)", expanded=False):
        c_adj1, c_adj2, c_adj3, c_adj4 = st.columns(4)
        with c_adj1: adj_width = st.slider("Largura da Tabela (%)", 90, 120, 105)
        with c_adj2: adj_margin_left = st.slider("Recuo Esquerdo (Margem Negativa %)", -10, 5, -3)
        with c_adj3: adj_margin_top = st.slider("Espaço Superior (Margem Negativa px)", -100, 0, -40)
        with c_adj4: adj_height = st.slider("Altura do Frame (px)", 400, 1500, 800)
        
        config_text = f"LARGURA: {adj_width}% | MARGEM_L: {adj_margin_left}% | MARGEM_T: {adj_margin_top}px | ALTURA: {adj_height}px"
        st.info(f"Ajuste os sliders até a tabela encostar nas bordas. CONFIG ATUAL: {config_text}")

    st.markdown(f"""
    <style>
    .ger-container-custom {{ 
        width: {adj_width}vw !important; 
        margin-left: {adj_margin_left}% !important;
        margin-top: {adj_margin_top}px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Filtros e Tabela
    st.markdown('<div style="padding: 0 20px;">', unsafe_allow_html=True)
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    with cf4:
        if st.button("🔄", key="btn_ref"): st.cache_data.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    df_g = safe_read()

    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False, na=False) | df_g['ID'].str.contains(bu, case=False, na=False)]
        
        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            sc = "status-badge status-ativo" if r['STATUS'] == "ATIVO" else "status-badge status-cancelado"
            rows += f"""
            <tr class="ger-row">
                <td><span class='{sc}'>{r['STATUS']}</span></td>
                <td>{r['UNID.']}</td>
                <td style='width: auto; white-space: nowrap;'>{r['TURMA']}</td>
                <td>{r['10C']}</td>
                <td>{r['ING']}</td>
                <td>{r['DT_CAD']}</td>
                <td class="ger-id">{r['ID']}</td>
                <td class="ger-nome">{r['ALUNO']}</td>
                <td>{r['TEL_RESP']}</td>
                <td>{r['TEL_ALU']}</td>
                <td>{r['CPF']}</td>
                <td>{r['CIDADE']}</td>
                <td class="ger-wrap">{r['CURSO']}</td>
                <td class="ger-wrap">{r['PAGTO']}</td>
                <td>{r['VEND.']}</td>
                <td>{r['DT_MAT']}</td>
            </tr>
            """

        html_code = f"""
        <style>
        body {{ background-color: #0b0e1e; color: #e0e0e0; font-family: Arial, sans-serif; margin: 0; padding: 0; overflow: auto; }}
        .ger-table {{ width: 100%; border-collapse: separate; border-spacing: 0 5px; min-width: 1900px; table-layout: fixed; }}
        .ger-table thead th {{ text-align: left; font-size: 11px; color: #00f2ff; padding: 8px 10px; text-transform: uppercase; position: sticky; top: 0; background: #0b0e1e; z-index: 10; }}
        .ger-row {{ background: rgba(18, 22, 41, 0.7); }}
        .ger-table td {{ padding: 10px 10px; font-size: 12px; color: #e0e0e0; border-top: 1px solid #1f295a; border-bottom: 1px solid #1f295a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .ger-nome {{ color: #00f2ff; font-weight: bold; font-size: 13px; }}
        .ger-id {{ color: #00f2ff; font-weight: bold; }}
        .ger-wrap {{ white-space: normal !important; word-wrap: break-word; }}
        .status-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }}
        .status-ativo {{ color: #2ecc71; border: 1px solid #2ecc71; }}
        .status-cancelado {{ color: #e74c3c; border: 1px solid #e74c3c; }}
        </style>
        <div class="ger-container">
            <table class="ger-table">
                <thead>
                    <tr>
                        <th style="width: 80px;">STATUS</th>
                        <th style="width: 50px;">UNID.</th>
                        <th style="width: 38px;">TURMA</th>
                        <th style="width: 40px;">10C</th>
                        <th style="width: 40px;">ING</th>
                        <th style="width: 90px;">DT_CAD</th>
                        <th style="width: 100px;">ID</th>
                        <th style="width: 180px;">ALUNO</th>
                        <th style="width: 110px;">TEL_RESP</th>
                        <th style="width: 110px;">TEL_ALU</th>
                        <th style="width: 120px;">CPF</th>
                        <th style="width: 100px;">CIDADE</th>
                        <th style="width: 220px;">CURSO</th>
                        <th style="width: 220px;">PAGTO</th>
                        <th style="width: 100px;">VEND.</th>
                        <th style="width: 90px;">DT_MAT</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        st.markdown('<div class="ger-container-custom">', unsafe_allow_html=True)
        components.html(html_code, height=adj_height, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    st.markdown('<div style="padding: 0 20px;">', unsafe_allow_html=True)
    st.info("Painel de relatórios simplificado.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    st.markdown('</div>', unsafe_allow_html=True)
