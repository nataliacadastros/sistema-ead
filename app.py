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
    .hud-bar-container { background: rgba(31, 41, 90, 0.3); height: 14px; border-radius: 20px; width: 100%; position: relative; margin: 50px 0 40px 0; border: 1px solid #1f295a; }
    .hud-segment { height: 100%; float: left; position: relative; }
    .hud-label { position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: #121629; border: 1px solid currentColor; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .hud-city-name { position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; text-transform: uppercase; white-space: nowrap; }
    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""

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
    st.session_state.val_curso = st.session_state.val_curso.upper().strip()
    st.session_state.input_curso_key = st.session_state.val_curso

def processar_pagto():
    base = st.session_state.f_pagto.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.get('chk_1'): obs.append("LIBERAÇÃO IN-GLÊS")
    if st.session_state.get('chk_2'): obs.append("CURSO BÔNUS")
    if st.session_state.get('chk_3'): obs.append("CONFIRMAÇÃO MATRÍCULA")
    st.session_state.f_pagto = f"{base} | {' | '.join(obs)}" if obs else base

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        c_id_lab, c_id_inp = st.columns([1.5, 3.5])
        c_id_lab.markdown("<label>ID:</label>", unsafe_allow_html=True)
        f_id = c_id_inp.text_input("ID", key="f_id", label_visibility="collapsed")

        c_nom_lab, c_nom_inp = st.columns([1.5, 3.5])
        c_nom_lab.markdown("<label>ALUNO:</label>", unsafe_allow_html=True)
        f_nome = c_nom_inp.text_input("ALUNO", key="f_nome", label_visibility="collapsed")

        c_tr_lab, c_tr_inp = st.columns([1.5, 3.5])
        c_tr_lab.markdown("<label>TEL. RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_tel_resp = c_tr_inp.text_input("TEL. RESP", key="f_tel_resp", label_visibility="collapsed")

        c_ta_lab, c_ta_inp = st.columns([1.5, 3.5])
        c_ta_lab.markdown("<label>TEL. ALUNO:</label>", unsafe_allow_html=True)
        f_tel_aluno = c_ta_inp.text_input("TEL. ALUNO", key="f_tel_aluno", label_visibility="collapsed")

        c_cpf_lab, c_cpf_inp = st.columns([1.5, 3.5])
        c_cpf_lab.markdown("<label>CPF RESPONSÁVEL:</label>", unsafe_allow_html=True)
        f_cpf = c_cpf_inp.text_input("CPF", key="f_cpf", label_visibility="collapsed")

        c_cid_lab, c_cid_inp = st.columns([1.5, 3.5])
        c_cid_lab.markdown("<label>CIDADE:</label>", unsafe_allow_html=True)
        f_cid = c_cid_inp.text_input("CIDADE", key="f_cid", label_visibility="collapsed")

        c_cur_lab, c_cur_inp = st.columns([1.5, 3.5])
        c_cur_lab.markdown("<label>CURSO CONTRATADO:</label>", unsafe_allow_html=True)
        f_curso = c_cur_inp.text_input("CURSO", key="input_curso_key", on_change=transformar_curso, label_visibility="collapsed")

        c_pag_lab, c_pag_inp = st.columns([1.5, 3.5])
        c_pag_lab.markdown("<label>FORMA DE PAGAMENTO:</label>", unsafe_allow_html=True)
        f_pagto = c_pag_inp.text_input("PAGAMENTO", key="f_pagto", label_visibility="collapsed")

        c_ven_lab, c_ven_inp = st.columns([1.5, 3.5])
        c_ven_lab.markdown("<label>VENDEDOR:</label>", unsafe_allow_html=True)
        f_vend = c_ven_inp.text_input("VENDEDOR", key="f_vend", label_visibility="collapsed")

        c_dat_lab, c_dat_inp = st.columns([1.5, 3.5])
        c_dat_lab.markdown("<label>DATA DA MATRÍCULA:</label>", unsafe_allow_html=True)
        # Inicializa data se não existir
        if "f_data" not in st.session_state: st.session_state.f_data = date.today().strftime("%d/%m/%Y")
        f_data = c_dat_inp.text_input("DATA", key="f_data", label_visibility="collapsed")

        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)

        st.write("")
        _, b_col1, b_col2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        with b_col1:
            if st.button("💾 SALVAR ALUNO"):
                if f_nome:
                    aluno = {
                        "ID": f_id.upper(), "Aluno": f_nome.upper(), "Tel_Resp": f_tel_resp,
                        "Tel_Aluno": f_tel_aluno, "CPF": f_cpf, "Cidade": f_cid.upper(),
                        "Curso": st.session_state.input_curso_key.strip(), "Pagto": f_pagto.upper(),
                        "Vendedor": f_vend.upper(), "Data_Mat": f_data
                    }
                    st.session_state.lista_previa.append(aluno)
                    
                    # LIMPEZA SELETIVA: Mantém Cidade, Curso, Vendedor e Data
                    limpar = ["f_id", "f_nome", "f_tel_resp", "f_tel_aluno", "f_cpf", "f_pagto", "chk_1", "chk_2", "chk_3"]
                    for k in limpar:
                        if k in st.session_state:
                            # Para checkboxes, resetar para False. Para texto, para vazio.
                            st.session_state[k] = False if "chk" in k else ""
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
                        
                        # LIMPEZA TOTAL: Zera absolutamente tudo
                        todas = ["f_id", "f_nome", "f_tel_resp", "f_tel_aluno", "f_cpf", "f_cid", 
                                 "input_curso_key", "f_pagto", "f_vend", "f_data", "chk_1", "chk_2", "chk_3"]
                        for k in todas:
                            if k in st.session_state:
                                st.session_state[k] = False if "chk" in k else ""
                        
                        st.success("Enviado com sucesso!")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

        st.write("---")
        st.markdown("<p style='color:#00f2ff; font-weight:bold; text-align:center;'>LISTA DE PRÉ-VISUALIZAÇÃO</p>", unsafe_allow_html=True)
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #00f2ff;'>🖥️ DATABASE MONITOR</h3>", unsafe_allow_html=True)
    try:
        dados_raw = conn.read(ttl="0s").fillna("")
        st.dataframe(dados_raw.iloc[::-1], use_container_width=True, hide_index=True, height=500)
        if st.button("🔄 REFRESH"): st.cache_data.clear(); st.rerun()
    except: st.error("Erro na conexão.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    try:
        df_raw = conn.read(ttl="0s").dropna(how='all')
        if not df_raw.empty:
            df_rel = df_raw.copy()
            col_names = ['STATUS', 'UNIDADE', 'TURMA', '10_CURSOS', 'INGLES', 'DATA_CAD', 'ID', 'ALUNO', 'T1', 'T2', 'CPF', 'CIDADE', 'CURSO', 'PAGAMENTO', 'VENDEDOR', 'DATA_MATRICULA']
            df_rel.columns = col_names[:len(df_rel.columns)]
            
            df_rel['DATA_MATRICULA'] = pd.to_datetime(df_rel['DATA_MATRICULA'], dayfirst=True, errors='coerce')
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel['DATA_MATRICULA'].dt.date >= intervalo[0]) & (df_rel['DATA_MATRICULA'].dt.date <= intervalo[1])].copy()
                df_f['Val_Rec'] = df_f['PAGAMENTO'].apply(extrair_valor_recebido)
                df_f['Val_Tick'] = df_f['PAGAMENTO'].apply(extrair_valor_geral)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"]=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="card-hud neon-red"><small>Canc.</small><h2>{len(df_f[df_f["STATUS"]=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:16px">R${df_f["Val_Rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c5:
                    tm_b = df_f[df_f['PAGAMENTO'].str.contains('BOLETO', na=False, case=False)]['Val_Tick'].mean() or 0.0
                    st.markdown(f'<div class="card-hud neon-purple"><small>T. Médio</small><div style="font-size:10px">Bol: R${tm_b:.0f}</div></div>', unsafe_allow_html=True)
                with c6:
                    top_v = df_f['VENDEDOR'].value_counts().idxmax() if not df_f.empty else "N/A"
                    st.markdown(f'<div class="card-hud neon-blue"><small>Top</small><h2 style="font-size:14px">{top_v}</h2></div>', unsafe_allow_html=True)

                st.write("---")
                df_cid_v = df_f['CIDADE'].value_counts().head(4)
                if not df_cid_v.empty:
                    st.markdown("<small style='color:#00f2ff'>▸ GEOLOCATION ANALYTICS</small>", unsafe_allow_html=True)
                    total_c = df_cid_v.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                    seg_html = "".join([f'<div class="hud-segment" style="width:{(q/total_c)*100}%; background:{cores[i%4]};"><div class="hud-label" style="color:{cores[i%4]};">{q}</div><div class="hud-city-name" style="color:{cores[i%4]};">{n}</div></div>' for i, (n, q) in enumerate(df_cid_v.items())])
                    st.markdown(f'<div class="hud-bar-container">{seg_html}</div>', unsafe_allow_html=True)

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_p = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b']))])
                    fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=350)
                    st.plotly_chart(fig_p, use_container_width=True)
                with col_g2:
                    df_v = df_f['VENDEDOR'].value_counts().reset_index().head(5)
                    fig_v = px.line(df_v, x='VENDEDOR', y='count', markers=True); fig_v.update_traces(line_color='#00f2ff')
                    fig_v.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
                    st.plotly_chart(fig_v, use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")
