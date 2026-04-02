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

    /* ESTILO CADASTRO */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 5px !important; display: flex; align-items: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    /* CARDS RELATÓRIO HUD */
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 100px; display: flex; flex-direction: column; justify-content: center; }
    .neon-pink { color: #ff007a; text-shadow: 0 0 10px rgba(255, 0, 122, 0.5); border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; text-shadow: 0 0 10px rgba(46, 204, 113, 0.5); border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5); border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.5); border-top: 2px solid #ff4b4b; }

    /* BARRA DE CIDADES HUD */
    .hud-bar-container { background: rgba(31, 41, 90, 0.3); height: 14px; border-radius: 20px; width: 100%; position: relative; margin: 50px 0 40px 0; border: 1px solid #1f295a; }
    .hud-segment { height: 100%; float: left; position: relative; }
    .hud-label { position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: #121629; border: 1px solid currentColor; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .hud-city-name { position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; text-transform: uppercase; white-space: nowrap; }

    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# --- FUNÇÕES AUXILIARES ---
def extrair_valor_recebido(texto):
    texto = str(texto).upper()
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', texto)
    if match:
        valor_str = match.group(1).replace('.', '').replace(',', '.')
        try: return float(valor_str)
        except: return 0.0
    return 0.0

def extrair_valor_geral(texto):
    try:
        valores = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(valores[0]) if valores else 0.0
    except: return 0.0

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

# --- ABAS DO SISTEMA ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        campos = [("ID:", "f_id"), ("ALUNO:", "f_nome"), ("CIDADE:", "f_cid"), 
                  ("CURSO:", "input_curso_key"), ("PAGAMENTO:", "input_pagto_key"), 
                  ("VENDEDOR:", "f_vend"), ("DATA MATRÍCULA:", "f_data")]
        for label, key in campos:
            c_lab, c_inp = st.columns([1.5, 3.5]) 
            c_lab.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if key == "input_curso_key": c_inp.text_input(label, key=key, value=st.session_state.val_curso, on_change=transformar_curso, label_visibility="collapsed")
            elif key == "input_pagto_key": c_inp.text_input(label, key=key, value=st.session_state.val_pagto, label_visibility="collapsed")
            elif key == "f_data": c_inp.text_input(label, key=key, value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")
            else: c_inp.text_input(label, key=key, label_visibility="collapsed")
        
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
                    aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), 
                             "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), 
                             "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), 
                             "Data Matrícula": st.session_state.f_data, "STATUS": "ATIVO"}
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        # --- CORREÇÃO DO ERRO APLICADA AQUI ---
                        creds_info = st.secrets["connections"]["gsheets"]
                        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
                        client = gspread.authorize(credentials)
                        
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        worksheet = sh.get_worksheet(0)
                        
                        df_new = pd.DataFrame(st.session_state.lista_previa)
                        novos_dados = df_new.values.tolist()
                        
                        col_a_values = worksheet.col_values(1)
                        ultima_linha_real = len(col_a_values)
                        
                        linha_inicio = ultima_linha_real + 2 if ultima_linha_real > 0 else 2
                        
                        worksheet.insert_rows(novos_dados, row=linha_inicio)
                        st.session_state.lista_previa = []
                        st.success(f"Dados inseridos com sucesso a partir da linha {linha_inicio}!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")

        st.write("---")
        st.markdown("<p style='color:#00f2ff; font-weight:bold; text-align:center;'>LISTA DE PRÉ-VISUALIZAÇÃO</p>", unsafe_allow_html=True)
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum aluno na lista de espera.")

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #00f2ff;'>🖥️ DATABASE MONITOR</h3>", unsafe_allow_html=True)
    try:
        dados = conn.read(ttl="0s").fillna("")
        if not dados.empty:
            if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
            st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=500)
            if st.button("🔄 REFRESH DATABASE"): st.cache_data.clear(); st.rerun()
    except: st.error("Erro na conexão.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    try:
        df_rel = conn.read(ttl="0s").dropna(how='all')
        if not df_rel.empty:
            df_rel.columns = [c.strip() for c in df_rel.columns]
            if 'Vendedor' in df_rel.columns:
                df_rel['Vendedor'] = df_rel['Vendedor'].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
            
            col_data = "Data Matrícula"
            df_rel[col_data] = pd.to_datetime(df_rel[col_data], dayfirst=True, errors='coerce')
            
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel[col_data].dt.date >= intervalo[0]) & (df_rel[col_data].dt.date <= intervalo[1])].copy()
                
                df_f['Valor_Recebido'] = df_f['Pagamento'].apply(extrair_valor_recebido)
                total_rec = df_f['Valor_Recebido'].sum()
                df_f['Valor_Ticket'] = df_f['Pagamento'].apply(extrair_valor_geral)
                df_bol = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]
                df_car = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK|CREDITO|DEBITO', na=False, case=False)]
                tm_bol = df_bol['Valor_Ticket'].mean() if not df_bol.empty else 0.0
                tm_car = df_car['Valor_Ticket'].mean() if not df_car.empty else 0.0

                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: 
                    atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{atv}</h2></div>', unsafe_allow_html=True)
                with c3:
                    cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="card-hud neon-red"><small>Cancelados</small><h2>{cnc}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${total_rec:,.2f}</h2></div>', unsafe_allow_html=True)
                with c5: st.markdown(f'<div class="card-hud neon-purple"><small>Ticket Médio</small><div style="font-size:11px; margin-top:5px">🎫 Bol: <b>R${tm_bol:.2f}</b><br>💳 Car: <b>R${tm_car:.2f}</b></div></div>', unsafe_allow_html=True)
                with c6:
                    top_v = df_f['Vendedor'].value_counts().idxmax() if not df_f.empty else "N/A"
                    st.markdown(f'<div class="card-hud neon-blue"><small>Top Captador</small><h2 style="font-size:14px">{top_v}</h2></div>', unsafe_allow_html=True)

                st.write("---")
                df_cid_v = df_f['Cidade'].value_counts().head(4)
                if not df_cid_v.empty:
                    st.markdown("<small style='color:#00f2ff'>▸ GEOLOCATION ANALYTICS</small>", unsafe_allow_html=True)
                    total_c = df_cid_v.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                    seg_html = ""
                    for i, (nome, qtd) in enumerate(df_cid_v.items()):
                        percent = (qtd / total_c) * 100; cor = cores[i % 4]
                        seg_html += f'<div class="hud-segment" style="width: {percent}%; background: {cor}; box-shadow: 0 0 10px {cor}80;"><div class="hud-label" style="color: {cor};">{qtd}</div><div class="hud-city-name" style="color: {cor};">{nome}</div></div>'
                    st.markdown(f'<div class="hud-bar-container">{seg_html}</div>', unsafe_allow_html=True)
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    counts = df_f['STATUS'].str.upper().value_counts()
                    fig_p = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b', '#00f2ff'], line=dict(color='#0b0e1e', width=3)), textinfo='label+value')])
                    fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=400)
                    st.plotly_chart(fig_p, use_container_width=True)
                with col_g2:
                    df_v = df_f['Vendedor'].value_counts().reset_index().head(5)
                    df_v.columns = ['Vendedor', 'Quantidade']
                    fig_v = px.line(df_v, x='Vendedor', y='Quantidade', markers=True, text='Vendedor')
                    fig_v.update_traces(line_color='#00f2ff', marker=dict(size=10, color='#ff007a', line=dict(width=2, color='white')), textposition="top center", mode='lines+markers+text')
                    fig_v.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, xaxis=dict(showgrid=False, showticklabels=False))
                    st.plotly_chart(fig_v, use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")
