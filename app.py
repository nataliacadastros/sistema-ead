import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- ARQUIVOS E PERSISTÊNCIA ---
ARQUIVO_TAGS = "tags_salvas.json" [cite: 1]
ARQUIVO_CIDADES = "cidades.xlsx" [cite: 1]

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}} [cite: 1]
    if os.path.exists(ARQUIVO_TAGS): [cite: 1]
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f: [cite: 2]
                conteudo = json.load(f) [cite: 2]
                if isinstance(conteudo, dict) and "tags" in conteudo: [cite: 2]
                    return conteudo [cite: 2]
                elif isinstance(conteudo, dict): [cite: 3]
                    return {"tags": conteudo, "last_selection": {}} [cite: 3]
        except: 
            return padrao [cite: 3]
    return padrao [cite: 3]

def salvar_tags(dados):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f: [cite: 3]
        json.dump(dados, f, ensure_ascii=False, indent=2) [cite: 3]

if "dados_tags" not in st.session_state: [cite: 3]
    st.session_state.dados_tags = carregar_tags() [cite: 3]

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", [cite: 3, 4]
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR", [cite: 4]
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO" [cite: 4]
}

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; } [cite: 4, 5]
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a; [cite: 5, 6]
        position: fixed; top: 0; left: 0 !important; width: 100vw !important; [cite: 6]
        z-index: 999; justify-content: center; height: 35px !important; [cite: 6, 7]
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; } [cite: 7, 8]
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; [cite: 8, 9]
    background-color: rgba(0, 242, 255, 0.05) !important; } [cite: 9]
    
    .main .block-container { padding-top: 40px !important; max-width: 98% !important; margin: 0 auto !important; } [cite: 9, 10]
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; } [cite: 10, 11, 12]
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; } [cite: 12, 13, 14]

    [data-testid="stDataFrame"] { height: 75vh !important; width: 100% !important; }

    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); } [cite: 22, 23, 24]
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; } [cite: 24, 25]
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; } [cite: 25]
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; } [cite: 25, 26]
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; } [cite: 26, 27]
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; } [cite: 27, 28]
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; transition: all 0.3s ease !important; } [cite: 28, 29, 30]
    header {visibility: hidden;} footer {visibility: hidden;} [cite: 31]
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; } [cite: 32, 33]
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection) [cite: 33]

def safe_read():
    try:
        df = conn.read(ttl="1s").dropna(how='all') [cite: 33]
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro de conexão: {e}") [cite: 33]
        return pd.DataFrame() [cite: 33]

# --- ESTADOS DE SESSÃO ---
if "history" not in st.session_state: st.session_state.history = []
if "history_idx" not in st.session_state: st.session_state.history_idx = -1
if "lista_previa" not in st.session_state: st.session_state.lista_previa = [] [cite: 33]
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0 [cite: 33]
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0 [cite: 34]

# --- FUNÇÕES DE SINCRONIZAÇÃO E HISTÓRICO ---
def sync_to_sheets(df):
    try:
        creds_info = st.secrets["connections"]["gsheets"] [cite: 47]
        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])) [cite: 48]
        sheet = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0) [cite: 48]
        df_sync = df.copy().fillna("")
        data_to_send = [df_sync.columns.values.tolist()] + df_sync.astype(str).values.tolist()
        sheet.update(data_to_send)
        st.cache_data.clear() [cite: 53]
    except Exception as e:
        st.error(f"Erro na sincronização: {e}") [cite: 54]

def add_to_history(df):
    st.session_state.history = st.session_state.history[:st.session_state.history_idx + 1]
    st.session_state.history.append(df.copy())
    if len(st.session_state.history) > 30: st.session_state.history.pop(0)
    st.session_state.history_idx = len(st.session_state.history) - 1

def handle_editor_change():
    new_df = st.session_state.df_gerenciamento
    sync_to_sheets(new_df)
    add_to_history(new_df)

# CORREÇÃO DEFINITIVA DO VALUEERROR
def extrair_valor_recebido(texto):
    if not texto: return 0.0 [cite: 34]
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper()) [cite: 34]
    if match:
        try:
            # Limpa qualquer caractere que não pertença ao número
            valor_limpo = match.group(1).replace('.', '').replace(',', '.')
            return float(valor_limpo) [cite: 35]
        except ValueError:
            return 0.0 [cite: 35]
    return 0.0 [cite: 35]

def extrair_valor_geral(texto):
    if not texto: return 0.0 [cite: 35]
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.')) [cite: 35]
        return float(v[0]) if v else 0.0 [cite: 35]
    except: return 0.0 [cite: 35]

def transformar_curso(chave):
    entrada = st.session_state[chave].strip() [cite: 35]
    if not entrada: return [cite: 35]
    match = re.search(r'(\d+)$', entrada) [cite: 36]
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo) [cite: 36, 37]
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip() [cite: 37]
            st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper() [cite: 37]
    else: st.session_state[chave] = entrada.upper() [cite: 37]

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave]) [cite: 37]
    if len(valor) == 11:
        st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}" [cite: 37]

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}" [cite: 38]
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip() [cite: 38]
    novo = base [cite: 38]
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês" [cite: 38]
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha" [cite: 38]
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA" [cite: 38, 39]
    st.session_state[f"f_pagto_{suffix}"] = novo.upper() [cite: 39]

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"]) [cite: 39]

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.2, 5.6, 0.2]) [cite: 39]
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}" [cite: 39]
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"), [cite: 39]
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"), [cite: 40]
                  ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"), [cite: 40]
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")] [cite: 40]
        
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8]) [cite: 40]
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True) [cite: 40]
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed") [cite: 41]
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed") [cite: 41]
            else: ci.text_input(l, key=k, label_visibility="collapsed") [cite: 41]
        
        st.write("")
        _, c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 1.2, 0.2]) [cite: 41]
        c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento) [cite: 41, 42]
        c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento) [cite: 42]
        c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento) [cite: 42]
        st.write("")
        _, b1, b2, _ = st.columns([1.2, 1.9, 1.9, 0.2]) [cite: 42]
        with b1:
            if st.button("💾 SALVAR ALUNO"): [cite: 42]
                if st.session_state[f"f_nome_{s_al}"]: [cite: 42]
                    st.session_state.lista_previa.append({ [cite: 43]
                        "ID": st.session_state[f"f_id_{s_al}"].upper(), [cite: 43]
                        "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), [cite: 43]
                        "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]), [cite: 43, 44]
                        "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), [cite: 44]
                        "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), [cite: 44, 45]
                        "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"] [cite: 45]
                    })
                    st.session_state.reset_aluno += 1; st.rerun() [cite: 46]
        with b2:
            if st.button("📤 ENVIAR PLANILHA"): [cite: 47]
                if st.session_state.lista_previa: [cite: 47]
                    try:
                        creds_info = st.secrets["connections"]["gsheets"] [cite: 47]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])) [cite: 48]
                        ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0) [cite: 48]
                        d_f = [[ "ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]] for a in st.session_state.lista_previa] [cite: 49, 50, 51, 52]
                        ws.append_rows(d_f, value_input_option='RAW') [cite: 52]
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1 [cite: 52, 53]
                        st.success("Enviado!"); st.cache_data.clear(); st.rerun() [cite: 53]
                    except Exception as e: st.error(f"Erro: {e}") [cite: 54]

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    c_undo, c_redo, c_search, c_st, c_un, c_ref = st.columns([0.3, 0.3, 2.0, 1.0, 1.0, 0.3]) [cite: 55]
    
    if c_undo.button("↩️"):
        if st.session_state.history_idx > 0:
            st.session_state.history_idx -= 1
            st.session_state.df_gerenciamento = st.session_state.history[st.session_state.history_idx].copy()
            sync_to_sheets(st.session_state.df_gerenciamento); st.rerun()
            
    if c_redo.button("↪️"):
        if st.session_state.history_idx < len(st.session_state.history) - 1:
            st.session_state.history_idx += 1
            st.session_state.df_gerenciamento = st.session_state.history[st.session_state.history_idx].copy()
            sync_to_sheets(st.session_state.df_gerenciamento); st.rerun()

    with c_search: bu = st.text_input("Buscar", placeholder="Nome ou ID", label_visibility="collapsed", key="search_ger") [cite: 55]
    with c_st: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], label_visibility="collapsed", key="status_ger") [cite: 55]
    with c_un: fu = st.selectbox("Unidade", ["Todos", "MGA"], label_visibility="collapsed", key="unid_ger") [cite: 55]
    with c_ref: 
        if st.button("🔄", key="ref_ger"): st.cache_data.clear(); st.rerun() [cite: 56]

    if "df_gerenciamento" not in st.session_state:
        df_raw = safe_read()
        if not df_raw.empty:
            st.session_state.df_gerenciamento = df_raw
            add_to_history(df_raw)

    if "df_gerenciamento" in st.session_state and not st.session_state.df_gerenciamento.empty:
        df_view = st.session_state.df_gerenciamento.copy()
        if bu: df_view = df_view[df_view['ALUNO'].str.contains(bu, case=False, na=False) | df_view['ID'].astype(str).str.contains(bu, case=False, na=False)] [cite: 56, 57]
        if fs != "Todos": df_view = df_view[df_view['STATUS'] == fs] [cite: 57]
        if fu != "Todos": df_view = df_view[df_view['UNID.'] == fu] [cite: 57]

        st.session_state.df_gerenciamento = st.data_editor(
            df_view,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "STATUS": st.column_config.SelectboxColumn("STATUS", options=["ATIVO", "CANCELADO"], required=True),
                "ID": st.column_config.TextColumn("ID", disabled=True),
            },
            key="editor_geral",
            on_change=handle_editor_change
        )

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read() [cite: 58]
    if not df_r.empty:
        dt_col = "DT_MAT" 
        if dt_col in df_r.columns:
            df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce') [cite: 58]
            iv = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY") [cite: 59]
            
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy() [cite: 59]
                col_pagto = "PAGTO" if "PAGTO" in df_r.columns else "PAGAMENTO"
                col_curso = "CURSO"; col_vend = "VENDEDOR"; col_cid = "CIDADE"

                df_f['v_rec'] = df_f[col_pagto].apply(extrair_valor_recebido) [cite: 59]
                df_f['v_tic'] = df_f[col_pagto].apply(extrair_valor_geral) [cite: 59]
                
                c1, c2, c3, c4, c5, c6 = st.columns(6) [cite: 60]
                with c1: st.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True) [cite: 60]
                with c2: st.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True) [cite: 60]
                with c3: st.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True) [cite: 60]
                with c4: st.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">TOTAL RECEBIDO</span><h2 style="font-size:22px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True) [cite: 60]
                with c5:
                    tm_b = df_f[df_f[col_pagto].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0 [cite: 61]
                    tm_c = df_f[df_f[col_pagto].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0 [cite: 61]
                    st.markdown(f'<div class="card-hud neon-purple"><span class="stat-label">TICKET MÉDIO</span><div style="font-size:18px; font-weight:bold; color:#e0e0e0;">BOL: R${tm_b:.0f}<br>CAR: R${tm_c:.0f}</div></div>', unsafe_allow_html=True) [cite: 61, 62]
                with c6:
                    c_banc = len(df_f[df_f[col_curso].str.contains("BANCÁRIO", case=False, na=False)]) [cite: 62]
                    c_agro = len(df_f[df_f[col_curso].str.contains("AGRO", case=False, na=False)]) [cite: 62]
                    c_ing = len(df_f[df_f[col_curso].str.contains("INGLÊS", case=False, na=False)]) [cite: 62, 63]
                    c_tec = len(df_f[df_f[col_curso].str.contains("TECNOLOGIA|INFORMÁTICA", case=False, na=False)]) [cite: 63]
                    st.markdown(f'''<div class="card-hud neon-blue"><span class="stat-label">POR ÁREA</span><div style="font-size:15px; text-align:left; color:#e0e0e0; line-height:1.4; padding-left:5px;">BANC: <b style="color:#00f2ff;">{c_banc}</b> | AGRO: <b style="color:#00f2ff;">{c_agro}</b><br>INGL: <b style="color:#00f2ff;">{c_ing}</b> | TECN: <b style="color:#00f2ff;">{c_tec}</b></div></div>''', unsafe_allow_html=True) [cite: 64, 65]

                st.write("")
                if not df_f.empty:
                    at_c = len(df_f[df_f["STATUS"].str.upper()=="ATIVO"]); can_c = len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"]) [cite: 66]
                    fig_status = go.Figure() [cite: 66]
                    fig_status.add_trace(go.Bar(y=["STATUS"], x=[at_c], orientation='h', marker=dict(color='#2ecc71'), text=[f"<b>ATIVOS: {at_c}</b>"], textposition='inside', insidetextanchor='start')) [cite: 66]
                    fig_status.add_trace(go.Bar(y=["STATUS"], x=[can_c], orientation='h', marker=dict(color='#ff4b4b'), text=[f"<b>CANCELADOS: {can_c}</b>"], textposition='inside', insidetextanchor='end')) [cite: 66]
                    fig_status.update_layout(barmode='stack', showlegend=False, height=40, margin=dict(t=5, b=5, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)) [cite: 67]
                    st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False}) [cite: 67]
                
                st.write("---")
                col_g1, col_g2 = st.columns(2) [cite: 67]
                with col_g1:
                    st.markdown("<h4 style='text-align:center; color:#00f2ff;'>📍 CIDADES E VENDEDORES</h4>", unsafe_allow_html=True) [cite: 67, 68]
                    df_city_full = df_f.copy() [cite: 68]
                    df_city_full["V_L"] = df_city_full[col_vend].str.split(" - ").str[0].str.strip() [cite: 68]
                    top_c = df_city_full[col_cid].value_counts().head(5).index [cite: 68]
                    city_data = [{"Cidade": c, "Qtd": len(df_city_full[df_city_full[col_cid] == c]), "Vendedores": ", ".join(list(df_city_full[df_city_full[col_cid] == c]["V_L"].unique()))} for c in top_c] [cite: 69, 70]
                    df_p = pd.DataFrame(city_data) [cite: 70]
                    fig = go.Figure(go.Bar(x=df_p['Cidade'], y=df_p['Qtd'], text=df_p.apply(lambda r: f"<b>{r['Qtd']}</b><br><span style='font-size:11px; color:#ff007a;'>{r['Vendedores']}</span>", axis=1), textposition='outside', marker=dict(color='#00f2ff'))) [cite: 70, 71, 72]
                    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450) [cite: 72]
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) [cite: 73]
                with col_g2:
                    st.markdown("<h4 style='text-align:center; color:#bc13fe;'>⚡ PERFORMANCE DE VENDAS</h4>", unsafe_allow_html=True) [cite: 73]
                    df_temp = df_f.copy() [cite: 73]
                    df_temp["V_L"] = df_temp[col_vend].str.split(" - ").str[0].str.strip() [cite: 73]
                    df_stats = df_temp["V_L"].value_counts().reset_index().head(5) [cite: 73]
                    df_stats.columns = ['Vendedor', 'Total'] [cite: 74]
                    fig_vend = go.Figure(go.Scatter(x=df_stats['Vendedor'], y=df_stats['Total'], mode='lines+markers+text', text=df_stats['Total'], textposition="top center", line=dict(color='#bc13fe', width=4, shape='spline'), marker=dict(size=12, color='#ffffff', line=dict(color='#bc13fe', width=3)), fill='tozeroy', fillcolor='rgba(188, 19, 254, 0.2)', textfont=dict(size=10, color="#bc13fe", family="Arial Black"))) [cite: 74, 75]
                    fig_vend.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(t=50, l=60, r=60), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", showticklabels=False)) [cite: 75]
                    st.plotly_chart(fig_vend, use_container_width=True, config={'displayModeBar': False}) [cite: 76]
        else: st.error("Coluna 'DT_MAT' não encontrada.")

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD") [cite: 76]
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True) [cite: 76]
    st.write("---") [cite: 76]
    if modo == "AUTOMÁTICO": [cite: 76]
        df_m = safe_read() [cite: 76]
        if not df_m.empty: [cite: 76]
            try:
                col_f = df_m.columns[5]; df_m[col_f] = pd.to_datetime(df_m[col_f], dayfirst=True, errors='coerce') [cite: 76, 77]
                data_sel = st.date_input("Filtrar Cadastro (Coluna F):", value=date.today()) [cite: 77]
                df_filtrado = df_m[df_m[col_f].dt.date == data_sel] [cite: 77]
                if not df_filtrado.empty: [cite: 77]
                    cids = sorted(df_filtrado[df_m.columns[11]].unique()) [cite: 77]
                    sel_cids = st.multiselect("Cidades:", cids) [cite: 78]
                    st.session_state.df_auto_ready = df_filtrado[df_filtrado[df_m.columns[11]].isin(sel_cids)] [cite: 78]
                    st.info(f"{len(st.session_state.df_auto_ready)} alunos encontrados.") [cite: 78]
            except: st.error("Erro ao processar colunas.") [cite: 78]
    else:
        c1, c2 = st.columns(2) [cite: 78]
        with c1:
            u_user = st.text_area("IDs", height=100, key="in_user"); u_cell = st.text_area("Celulares", height=100, key="in_cell") [cite: 79]
            u_city = st.text_area("Cidades", height=100, key="in_city"); u_pay = st.text_area("Pagamentos", height=100, key="in_pay") [cite: 79, 80]
        with c2:
            u_nome = st.text_area("Nomes", height=100, key="in_nome"); u_doc = st.text_area("Documentos", height=100, key="in_doc") [cite: 80, 81]
            u_cour = st.text_area("Cursos", height=100, key="in_cour"); u_sell = st.text_area("Vendedores", height=100, key="in_sell") [cite: 81, 82]
        u_date = st.text_area("Datas", height=100, key="in_date") [cite: 82]

    with st.expander("🛠️ CONFIGURAR TAGS", expanded=False): [cite: 82]
        cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRAÇÃO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA'] [cite: 82]
        cols = st.columns(3); selected_tags = {} [cite: 82, 83]
        for i, curso in enumerate(cursos_tags):
            with cols[i % 3]:
                st.markdown(f"<p style='font-size:10px; margin-bottom:2px; color:#00f2ff; font-weight:bold;'>{curso}</p>", unsafe_allow_html=True) [cite: 83]
                tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, []) [cite: 83]
                last_sel = st.session_state.dados_tags.get("last_selection", {}).get(curso, "") [cite: 83]
                idx_default = (tags_lista.index(last_sel) + 1) if last_sel in tags_lista else 0 [cite: 84]
                c_sel, c_del = st.columns([0.4, 0.6]) [cite: 84]
                cur_tag = c_sel.selectbox("", [""] + tags_lista, index=idx_default, key=f"sel_{curso}", label_visibility="collapsed") [cite: 84]
                if cur_tag != last_sel:
                    st.session_state.dados_tags["last_selection"][curso] = cur_tag; salvar_tags(st.session_state.dados_tags) [cite: 84, 85]
                if c_del.button("🗑️", key=f"del_{curso}"): [cite: 85]
                    if cur_tag and cur_tag in st.session_state.dados_tags["tags"][curso]:
                        st.session_state.dados_tags["tags"][curso].remove(cur_tag) [cite: 85, 86]
                        st.session_state.dados_tags["last_selection"][curso] = ""; salvar_tags(st.session_state.dados_tags); st.rerun() [cite: 86]
                c_new, _ = st.columns([0.4, 0.6]); new_tag = c_new.text_input("", placeholder="Nova...", key=f"new_{i}", label_visibility="collapsed").upper() [cite: 86, 87]
                if new_tag and new_tag not in tags_lista: [cite: 87]
                    if "tags" not in st.session_state.dados_tags: st.session_state.dados_tags["tags"] = {} [cite: 87]
                    if curso not in st.session_state.dados_tags["tags"]: st.session_state.dados_tags["tags"][curso] = [] [cite: 87]
                    st.session_state.dados_tags["tags"][curso].append(new_tag); st.session_state.dados_tags["last_selection"][curso] = new_tag; salvar_tags(st.session_state.dados_tags); st.rerun() [cite: 88]
                selected_tags[curso] = (new_tag if new_tag else cur_tag).upper() [cite: 88, 89]

    if st.button("🚀 PROCESSAR DADOS", use_container_width=True): [cite: 89]
        raw_list = [] [cite: 89]
        if modo == "MANUAL": [cite: 89]
            l_ids = u_user.strip().split('\n'); l_nomes = u_nome.strip().split('\n'); l_pays = u_pay.strip().split('\n') [cite: 89, 90]
            l_cours = u_cour.strip().split('\n'); l_cells = u_cell.strip().split('\n'); l_docs = u_doc.strip().split('\n') [cite: 90, 91]
            l_citys = u_city.strip().split('\n'); l_sells = u_sell.strip().split('\n'); l_dates = u_date.strip().split('\n') [cite: 91, 92]
            for i in range(len(l_ids)):
                try: raw_list.append({"User": l_ids[i], "Nome": l_nomes[i] if i < len(l_nomes) else "", "Pay": l_pays[i] if i < len(l_pays) else "", "Cour": l_cours[i] if i < len(l_cours) else "", "Cell": l_cells[i] if i < len(l_cells) else "", "Doc": l_docs[i] if i < len(l_docs) else "", "City": l_citys[i] if i < len(l_citys) else "", "Sell": l_sells[i] if i < len(l_sells) else "", "Date": l_dates[i] if i < len(l_dates) else ""}) [cite: 92, 93]
                except: continue [cite: 93]
        elif "df_auto_ready" in st.session_state and st.session_state.df_auto_ready is not None: [cite: 93]
            for _, r in st.session_state.df_auto_ready.iterrows(): [cite: 93]
                raw_list.append({"User": r.iloc[6], "Nome": r.iloc[7], "Cell": r.iloc[9], "Doc": r.iloc[10], "City": r.iloc[11], "Cour": r.iloc[12], "Pay": r.iloc[13], "Sell": r.iloc[14], "Date": r.iloc[15]}) [cite: 93, 94]
        
        if raw_list:
            try:
                wb_c = load_workbook(ARQUIVO_CIDADES); ws_c = wb_c.active [cite: 94, 95]
                c_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]} [cite: 95]
            except: c_map = {} [cite: 95]
            processed = [] [cite: 95]
            for item in raw_list:
                c_orig = str(item['Cour']).upper(); p_orig = str(item['Pay']).upper() [cite: 95, 96]
                tags_f = [selected_tags[k] for k in cursos_tags if k in c_orig and selected_tags.get(k)] [cite: 96]
                c_final = ",".join(tags_f).upper() if tags_f else c_orig [cite: 96]
                p_final = "PENDENTE"; has_bol = "BOLETO" in p_orig; has_car = "CARTÃO" in p_orig or "LINK" in p_orig [cite: 96, 97]
                if (has_bol and not has_car): p_final = "BOLETO" [cite: 97]
                elif (has_car and not has_bol): p_final = "CARTÃO" [cite: 97]
                obs_final = f"{c_final} | {c_orig} | {p_orig}".upper(); ouro_val = "1" if "10 CURSOS PROFISSIONALIZANTES" in obs_final else "0" [cite: 97, 98]
                processed.append({"username": item['User'], "email2": f"{item['User']}@profissionalizaead.com.br", "name": str(item['Nome']).split(" ")[0].upper(), "lastname": " ".join(str(item['Nome']).split(" ")[1:]).upper(), "cellphone2": str(item['Cell']), "document": item['Doc'], "city2": c_map.get(str(item['City']).upper(), item['City']), "courses": c_final, "payment": p_final, "observation": obs_final, "ouro": ouro_val, "password": "futuro", "role": "1", "secretary": "MGA", "seller": item['Sell'], "contract_date": item['Date'], "active": "1"}) [cite: 98]
            st.session_state.df_final_processado = pd.DataFrame(processed) [cite: 98]

    if st.session_state.df_final_processado is not None:
        df = st.session_state.df_final_processado; mask = df['payment'] == "PENDENTE" [cite: 98, 99]
        if mask.any():
            st.warning("⚠️ Confirmação necessária:") [cite: 99]
            df_conf = df.loc[mask, ["username", "name", "observation"]].copy(); df_conf.columns = ["ID", "Nome", "Texto Original (Pagamento)"]; df_conf["Forma Final"] = "BOLETO" [cite: 99, 100]
            edited = st.data_editor(df_conf, column_config={"Forma Final": st.column_config.SelectboxColumn("Forma", options=["BOLETO", "CARTÃO"], required=True)}, disabled=["ID", "Nome", "Texto Original (Pagamento)"], hide_index=True, use_container_width=True, key="pag_editor") [cite: 100]
            if st.button("✅ CONFIRMAR E GERAR EXCEL"): [cite: 100]
                for _, row in edited.iterrows(): df.loc[df['username'] == row["ID"], "payment"] = row["Forma Final"] [cite: 100]
                st.session_state.df_final_processado = df; st.rerun() [cite: 100, 101]
        if not (st.session_state.df_final_processado['payment'] == "PENDENTE").any(): [cite: 101]
            output = BytesIO(); wb = Workbook(); ws = wb.active; ws.append(list(st.session_state.df_final_processado.columns)) [cite: 101, 102]
            for r in st.session_state.df_final_processado.values.tolist(): ws.append([str(val) for val in r]) [cite: 102]
            wb.save(output); st.download_button("📥 BAIXAR EXCEL FINAL", output.getvalue(), f"ead_{date.today()}.xlsx", use_container_width=True) [cite: 102, 103]
