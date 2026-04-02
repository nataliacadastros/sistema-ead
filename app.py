import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS CONSOLIDADO (CADASTRO FIEL AO ORIGINAL + RELATÓRIO INFOGRÁFICO) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    /* MENU SLIM NO TOPO */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a3a5a; border-bottom: 2px solid #2c5282;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 32px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; font-weight: 600; padding: 0px 30px !important; height: 32px !important; line-height: 32px !important; font-size: 13px !important; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #2ecc71 !important; }
    
    .main .block-container { padding-top: 38px !important; max-width: 1100px !important; margin: 0 auto !important; }

    /* --- ESTILO ABA CADASTRO (RESTAURADO) --- */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 3px !important; display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; width: 100% !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 15px !important; padding-right: 15px !important; height: 25px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stCheckbox { display: flex; justify-content: center; margin-top: 8px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    .stButton > button { background-color: #2ecc71 !important; color: white !important; font-weight: bold !important; border-radius: 5px !important; }

    /* --- ESTILO ABA RELATÓRIO (INFOGRÁFICO) --- */
    .info-card { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; color: white; margin-bottom: 10px; border-bottom: 4px solid rgba(0,0,0,0.2); }
    .card-pink { background: linear-gradient(90deg, #FF00FF, #800080); }
    .card-green { background: linear-gradient(90deg, #00FF00, #008000); }
    .card-blue { background: linear-gradient(90deg, #00FFFF, #0000FF); }
    .card-orange { background: linear-gradient(90deg, #FFA500, #FF4500); }
    .titulo-rel { color: #FF00FF; font-weight: bold; font-size: 14px; margin-top: 20px; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# --- FUNÇÕES ---
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
    st.session_state.val_curso = st.session_state.val_curso.upper().strip() + " "
    st.session_state.input_curso_key = st.session_state.val_curso

def processar_pagto():
    base = st.session_state.input_pagto_key.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_1: obs.append("LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CURSO BÔNUS")
    if st.session_state.chk_3: obs.append("CONFIRMAÇÃO MATRÍCULA")
    st.session_state.val_pagto = f"{base} | {' | '.join(obs)}" if obs else base
    st.session_state.input_pagto_key = st.session_state.val_pagto

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO (RESTAURADA) ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        campos = [("ID:", "f_id", None), ("ALUNO:", "f_nome", None), ("CIDADE:", "f_cid", None), ("CURSO:", "input_curso_key", transformar_curso), ("PAGAMENTO:", "input_pagto_key", None), ("VENDEDOR:", "f_vend", None), ("DATA MATRÍCULA:", "f_data", None)]
        for label, key, func in campos:
            c_lab, c_inp = st.columns([1.5, 3.5]) 
            c_lab.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if key == "input_curso_key": c_inp.text_input(label, key=key, value=st.session_state.val_curso, on_change=func, label_visibility="collapsed")
            elif key == "input_pagto_key": c_inp.text_input(label, key=key, value=st.session_state.val_pagto, label_visibility="collapsed")
            elif key == "f_data": c_inp.text_input(label, key=key, value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")
            else: c_inp.text_input(label, key=key, label_visibility="collapsed")
        
        _, c_c1, c_c2, c_c3, _ = st.columns([0.8, 1.2, 1.2, 1.2, 0.8])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)
        
        st.write("")
        _, b_l, b_r, _ = st.columns([0.5, 2, 2, 0.5])
        with b_l:
            if st.button("💾 SALVAR ALUNO", key="btn_save"):
                if st.session_state.f_nome:
                    aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), "Data Matrícula": st.session_state.f_data}
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with b_r:
            if st.button("📤 ENVIAR PLANILHA", key="btn_send"):
                if st.session_state.lista_previa:
                    df_old = conn.read(ttl="0s").fillna(""); df_new = pd.DataFrame(st.session_state.lista_previa)
                    conn.update(data=pd.concat([df_old, df_new], ignore_index=True))
                    st.session_state.lista_previa = []; st.success("Enviado!"); st.rerun()
        
        st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO (RESTAURADA) ---
with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #2ecc71;'>🖥️ BASE DE DADOS</h3>", unsafe_allow_html=True)
    try:
        dados = conn.read(ttl="0s").fillna("")
        if not dados.empty:
            if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
            st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=500)
            if st.button("🔄 ATUALIZAR LISTA"): st.cache_data.clear(); st.rerun()
    except: st.error("Erro ao carregar dados.")

# --- ABA 3: RELATÓRIOS (ESTILO INFOGRÁFICO) ---
with tab_rel:
    try:
        df_rel = conn.read(ttl="0s").dropna(how='all')
        if not df_rel.empty:
            df_rel.columns = [c.strip() for c in df_rel.columns]
            col_data = "Data Matrícula"
            df_rel[col_data] = pd.to_datetime(df_rel[col_data], dayfirst=True, errors='coerce')
            
            st.markdown("<p style='color: #2ecc71; font-weight: bold;'>Selecione o período:</p>", unsafe_allow_html=True)
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY", label_visibility="collapsed")
            
            if isinstance(intervalo, (tuple, list)) and len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel[col_data].dt.date >= intervalo[0]) & (df_rel[col_data].dt.date <= intervalo[1])]
                
                # TOP CARDS
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="info-card card-pink"><small>MATRÍCULAS</small><br><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: 
                    atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="info-card card-green"><small>ATIVOS</small><br><h2>{atv}</h2></div>', unsafe_allow_html=True)
                with c3:
                    cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="info-card card-blue"><small>CANCELADOS</small><br><h2>{cnc}</h2></div>', unsafe_allow_html=True)
                with c4:
                    vend = df_f['Vendedor'].nunique() if 'Vendedor' in df_f.columns else 0
                    st.markdown(f'<div class="info-card card-orange"><small>VENDEDORES</small><br><h2>{vend}</h2></div>', unsafe_allow_html=True)

                st.write("---")
                g1, g2 = st.columns([1, 1.2])
                with g1:
                    st.markdown('<p class="titulo-rel">▸ Statistics and analysis</p>', unsafe_allow_html=True)
                    if 'STATUS' in df_f.columns:
                        fig_p = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=.7, marker=dict(colors=['#FF00FF', '#00FFFF', '#FFA500']))])
                        fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=350, margin=dict(t=0,b=0,l=0,r=0))
                        fig_p.update_traces(textinfo='label+percent', textposition='inside')
                        st.plotly_chart(fig_p, use_container_width=True)
                with g2:
                    st.markdown('<p class="titulo-rel">▸ Charts and Graphs</p>', unsafe_allow_html=True)
                    df_cid = df_f['Cidade'].value_counts().reset_index()
                    fig_c = px.bar(df_cid, x='count', y='Cidade', orientation='h', color='count', color_continuous_scale='Magma')
                    fig_c.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, showlegend=False)
                    st.plotly_chart(fig_c, use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")
