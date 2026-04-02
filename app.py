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

# --- INICIALIZAÇÃO DE ESTADOS ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "f_id" not in st.session_state: st.session_state.f_id = ""
if "f_nome" not in st.session_state: st.session_state.f_nome = ""
if "f_cid" not in st.session_state: st.session_state.f_cid = ""
if "f_curso" not in st.session_state: st.session_state.f_curso = ""
if "f_pagto" not in st.session_state: st.session_state.f_pagto = ""
if "f_vend" not in st.session_state: st.session_state.f_vend = ""
if "f_data" not in st.session_state: st.session_state.f_data = date.today().strftime("%d/%m/%Y")

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
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
    .main .block-container { padding-top: 45px !important; max-width: 1200px !important; margin: 0 auto !important; }
    div[data-testid="stHorizontalBlock"] { margin-bottom: 5px !important; display: flex; align-items: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 100px; display: flex; flex-direction: column; justify-content: center; }
    .neon-pink { color: #ff007a; text-shadow: 0 0 10px rgba(255, 0, 122, 0.5); border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; text-shadow: 0 0 10px rgba(46, 204, 113, 0.5); border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5); border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.5); border-top: 2px solid #ff4b4b; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    .hud-bar-container { background: rgba(31, 41, 90, 0.3); height: 14px; border-radius: 20px; width: 100%; position: relative; margin: 50px 0 40px 0; border: 1px solid #1f295a; }
    .hud-segment { height: 100%; float: left; position: relative; }
    .hud-label { position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: #121629; border: 1px solid currentColor; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .hud-city-name { position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; text-transform: uppercase; white-space: nowrap; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE LOGICA ---
def extrair_v_recebido(t):
    t = str(t).upper()
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', t)
    if match:
        v = match.group(1).replace('.', '').replace(',', '.')
        try: return float(v)
        except: return 0.0
    return 0.0

def extrair_v_geral(t):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(t).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def transformar_curso():
    entrada = st.session_state.f_curso_input.strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1)
        nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state.f_curso = f"{base} + {nome}".upper() if base and nome.upper() not in base.upper() else nome.upper()
        else: st.session_state.f_curso = entrada.upper()
    else: st.session_state.f_curso = entrada.upper()

def processar_pagto():
    base = st.session_state.f_pagto_input.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_1: obs.append("LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CURSO BÔNUS")
    if st.session_state.chk_3: obs.append("CONFIRMAÇÃO MATRÍCULA")
    st.session_state.f_pagto = f"{base} | {' | '.join(obs)}" if obs else base

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        # Campos de Cadastro
        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ID:</label>", unsafe_allow_html=True)
        st.session_state.f_id = c_inp.text_input("ID", value=st.session_state.f_id, key="f_id_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        st.session_state.f_nome = c_inp.text_input("ALUNO", value=st.session_state.f_nome, key="f_nome_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        st.session_state.f_cid = c_inp.text_input("CIDADE", value=st.session_state.f_cid, key="f_cid_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        st.session_state.f_curso = c_inp.text_input("CURSO", value=st.session_state.f_curso, key="f_curso_input", on_change=transformar_curso, label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        st.session_state.f_pagto = c_inp.text_input("PAGAMENTO", value=st.session_state.f_pagto, key="f_pagto_input", on_change=processar_pagto, label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        st.session_state.f_vend = c_inp.text_input("VENDEDOR", value=st.session_state.f_vend, key="f_vend_input", label_visibility="collapsed")

        c_lab, c_inp = st.columns([1.5, 3.5])
        c_lab.markdown("<label>DATA MATRÍCULA:</label>", unsafe_allow_html=True)
        st.session_state.f_data = c_inp.text_input("DATA", value=st.session_state.f_data, key="f_data_input", label_visibility="collapsed")

        # Checkboxes S1, S2, S3
        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        _, b_col1, b_col2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        
        with b_col1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.f_nome:
                    aluno = {
                        "ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), 
                        "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.f_curso.upper(), 
                        "Pagamento": st.session_state.f_pagto.upper(), "Vendedor": st.session_state.f_vend.upper(), 
                        "Data Matrícula": st.session_state.f_data, "STATUS": "ATIVO"
                    }
                    st.session_state.lista_previa.append(aluno)
                    # Limpeza seletiva conforme solicitado
                    st.session_state.f_id = ""
                    st.session_state.f_nome = ""
                    st.session_state.f_curso = ""
                    st.session_state.f_pagto = ""
                    st.rerun()

        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
                        client = gspread.authorize(creds)
                        sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                        ws = sh.get_worksheet(0)
                        
                        dados = pd.DataFrame(st.session_state.lista_previa).values.tolist()
                        ultima = len(ws.col_values(1))
                        linha = ultima + 2 if ultima > 0 else 2
                        ws.insert_rows(dados, row=linha)
                        
                        # Limpa TUDO após enviar
                        st.session_state.lista_previa = []
                        st.session_state.f_id = ""
                        st.session_state.f_nome = ""
                        st.session_state.f_cid = ""
                        st.session_state.f_curso = ""
                        st.session_state.f_pagto = ""
                        st.session_state.f_vend = ""
                        st.session_state.f_data = date.today().strftime("%d/%m/%Y")
                        st.success("Enviado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

        st.write("---")
        if st.session_state.lista_previa:
            st.markdown("<p style='color:#00f2ff; font-weight:bold; text-align:center;'>PRÉ-VISUALIZAÇÃO</p>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_ger = conn.read(ttl="0s").fillna("")
        if not df_ger.empty:
            st.dataframe(df_ger.iloc[::-1], use_container_width=True, hide_index=True, height=500)
    except: st.error("Erro na conexão com a planilha.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_rel = conn.read(ttl="0s").dropna(how='all')
        if not df_rel.empty:
            df_rel.columns = [c.strip() for c in df_rel.columns]
            df_rel["Data Matrícula"] = pd.to_datetime(df_rel["Data Matrícula"], dayfirst=True, errors='coerce')
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel["Data Matrícula"].dt.date >= intervalo[0]) & (df_rel["Data Matrícula"].dt.date <= intervalo[1])].copy()
                df_f['Valor_Recebido'] = df_f['Pagamento'].apply(extrair_v_recebido)
                df_f['Valor_Ticket'] = df_f['Pagamento'].apply(extrair_v_geral)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                c2.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{atv}</h2></div>', unsafe_allow_html=True)
                cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df_f.columns else 0
                c3.markdown(f'<div class="card-hud neon-red"><small>Cancelados</small><h2>{cnc}</h2></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2>R${df_f["Valor_Recebido"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                c5.markdown(f'<div class="card-hud neon-purple"><small>Ticket</small><h6>B: R${df_f["Valor_Ticket"].mean():.2f}</h6></div>', unsafe_allow_html=True)
                venda = df_f['Vendedor'].value_counts().idxmax() if not df_f.empty else "N/A"
                c6.markdown(f'<div class="card-hud neon-blue"><small>Top</small><h6>{venda}</h6></div>', unsafe_allow_html=True)

                st.write("---")
                df_cid_v = df_f['Cidade'].value_counts().head(4)
                if not df_cid_v.empty:
                    st.markdown("<small style='color:#00f2ff'>▸ GEOLOCATION ANALYTICS</small>", unsafe_allow_html=True)
                    total_c = df_cid_v.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                    seg_html = "".join([f'<div class="hud-segment" style="width: {(v/total_c)*100}%; background: {cores[i%4]}; box-shadow: 0 0 10px {cores[i%4]}80;"><div class="hud-label" style="color: {cores[i%4]};">{v}</div><div class="hud-city-name" style="color: {cores[i%4]};">{k}</div></div>' for i, (k,v) in enumerate(df_cid_v.items())])
                    st.markdown(f'<div class="hud-bar-container">{seg_html}</div>', unsafe_allow_html=True)

                g1, g2 = st.columns(2)
                with g1:
                    st.plotly_chart(go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b', '#00f2ff']))]).update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False), use_container_width=True)
                with g2:
                    df_v = df_f['Vendedor'].value_counts().reset_index().head(5)
                    df_v.columns = ['Vendedor', 'count']
                    fig_v = px.line(df_v, x='Vendedor', y='count', markers=True, text='Vendedor')
                    fig_v.update_traces(line_color='#00f2ff', marker=dict(size=10, color='#ff007a'), textposition="top center", mode='lines+markers+text')
                    st.plotly_chart(fig_v.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, showticklabels=False)), use_container_width=True)
    except: st.error("Erro ao carregar relatórios.")
