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
    
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    
    div[data-testid="stTextInput"] { width: 55% !important; }
    .stTextInput input { 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        font-size: 12px !important; 
        height: 18px !important; 
        border-radius: 5px !important; 
    }
    
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .custom-table-wrapper {
        width: 100%; max-height: 600px; overflow: auto !important;
        background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px;
    }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }
    .custom-table tr:hover { background-color: rgba(0, 242, 255, 0.1); }
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 100px; display: flex; flex-direction: column; justify-content: center; }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    .hud-bar-container { background: rgba(31, 41, 90, 0.3); height: 14px; border-radius: 20px; width: 100%; position: relative; margin: 50px 0 40px 0; border: 1px solid #1f295a; }
    .hud-segment { height: 100%; float: left; position: relative; }
    .hud-label { position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: #121629; border: 1px solid currentColor; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .hud-city-name { position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; text-transform: uppercase; white-space: nowrap; }

    /* ESTILO DO BOTÃO LÁPIS DENTRO DA TABELA */
    div[data-testid="column"] button {
        background: transparent !important; border: none !important; color: #00f2ff !important;
        padding: 0 !important; width: 25px !important; height: 25px !important; min-height: 0px !important;
    }
    div[data-testid="column"] button:hover { color: #ff007a !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "id_edit" not in st.session_state: st.session_state.id_edit = None
if "aba_selecionada" not in st.session_state: st.session_state.aba_selecionada = 0

# --- FUNÇÕES ---
def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0

def extrair_valor_geral(texto):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

# --- NAVEGAÇÃO ---
# Se clicarmos no lápis, forçamos a aba 1 (Gerenciamento)
aba_inicial = st.session_state.aba_selecionada
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.session_state.aba_selecionada = 0
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        # (Lógica original do seu cadastro permanece intacta aqui)
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        c = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
             ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
             ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
             ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in c:
            cl, ci = st.columns([1.5, 3.5])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            ci.text_input(l, key=k, label_visibility="collapsed")
        
        if st.button("💾 SALVAR ALUNO"):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                st.session_state.reset_aluno += 1; st.rerun()

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.session_state.aba_selecionada = 1
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    bu = cf1.text_input("🔍 Buscar...", placeholder="Nome ou ID", label_visibility="collapsed")
    fs = cf2.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], label_visibility="collapsed")
    fu = cf3.selectbox("Unidade", ["Todos", "MGA"], label_visibility="collapsed")
    if cf4.button("🔄"): st.cache_data.clear(); st.rerun()

    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        
        # Filtros
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]

        # TABELA COM BOTÃO EDITAR NATIVO (Sem quebra de linha)
        st.markdown('<div class="custom-table-wrapper">', unsafe_allow_html=True)
        # Cabeçalho manual para alinhar com as colunas do Streamlit
        h_cols = st.columns([0.4, 1.2, 0.8, 1, 0.8, 0.8, 1, 3, 2, 2, 2, 2, 3, 4, 2, 2])
        for col, h_name in zip(h_cols, hd): col.markdown(f"<small><b>{h_name}</b></small>", unsafe_allow_html=True)
        
        for i, r in df_g.iloc[::-1].iterrows():
            r_cols = st.columns([0.4, 1.2, 0.8, 1, 0.8, 0.8, 1, 3, 2, 2, 2, 2, 3, 4, 2, 2])
            
            # O Lápis agora é um st.button real
            if r_cols[0].button("✏️", key=f"edit_{r['ID']}_{i}"):
                st.session_state.id_edit = r['ID']
                st.rerun()
            
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            r_cols[1].markdown(f"<span class='status-badge {sc}'>{r['STATUS']}</span>", unsafe_allow_html=True)
            r_cols[2].write(r['UNID.'])
            r_cols[6].markdown(f"<span style='color:#00f2ff;font-weight:bold'>{r['ID']}</span>", unsafe_allow_html=True)
            r_cols[7].markdown(f"<span style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</span>", unsafe_allow_html=True)
            r_cols[12].write(r['CURSO'])
            r_cols[13].write(r['PAGTO'])
            # (Preencha as outras r_cols conforme sua necessidade de visualização)

        # FRAME DE EDIÇÃO (Abaixo da tabela)
        if st.session_state.id_edit:
            st.write("---")
            st.subheader(f"🛠️ EDITAR: {st.session_state.id_edit}")
            aluno = df_g[df_g['ID'] == st.session_state.id_edit].iloc[0]
            
            with st.form("form_edit"):
                c1, c2, c3 = st.columns(3)
                e_status = c1.selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if aluno['STATUS']=="ATIVO" else 1)
                e_unid = c2.text_input("UNID.", value=aluno['UNID.'])
                e_turma = c3.text_input("TURMA", value=aluno['TURMA'])
                
                e_nome = st.text_input("NOME", value=aluno['ALUNO'])
                e_pagto = st.text_area("PAGAMENTO", value=aluno['PAGTO'])
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("✅ SALVAR"):
                    creds = st.secrets["connections"]["gsheets"]
                    client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
                    cell = ws.find(st.session_state.id_edit, in_col=7)
                    if cell:
                        ws.update_cell(cell.row, 1, e_status)
                        ws.update_cell(cell.row, 2, e_unid.upper())
                        ws.update_cell(cell.row, 8, e_nome.upper())
                        ws.update_cell(cell.row, 14, e_pagto.upper())
                        st.success("Atualizado!"); st.session_state.id_edit = None; st.cache_data.clear(); st.rerun()
                if b2.form_submit_button("❌ FECHAR"):
                    st.session_state.id_edit = None; st.rerun()

    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    st.session_state.aba_selecionada = 2
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            # (Todo o seu código original de gráficos e cartões HUD aqui)
            df_r.columns = [c.strip() for c in df_r.columns]; v_col = "Vendedor"
            dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            df_f = df_r.copy() # Simplificado para exemplo, mantenha sua lógica de filtro original
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"]=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            # ... (Restante dos cartões e gráficos originais)

    except Exception as e: st.error(f"Erro: {e}")
