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
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

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
        except: return padrao
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
    [data-testid="stAppViewBlockContainer"] { padding-top: 40px !important; padding-left: 10px !important; padding-right: 10px !important; max-width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #121629; border-bottom: 1px solid #1f295a; position: fixed; top: 0; left: 0 !important; width: 100vw !important; z-index: 999; justify-content: center; height: 35px !important; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .logo-container { position: relative; top: -10px; left: 0px; margin-bottom: 10px; }
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    .ag-theme-balham-dark {
        --ag-header-background-color: #1f295a;
        --ag-header-foreground-color: #00f2ff;
        --ag-background-color: #121629;
        --ag-row-hover-color: rgba(0, 242, 255, 0.1);
        --ag-selected-row-background-color: rgba(0, 242, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists(caminho_logo):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(caminho_logo, width=90)
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
def safe_read():
    try: return conn.read(ttl=0).dropna(how='all')
    except: return pd.DataFrame()

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

def extrair_valor_geral(texto):
    if not texto: return 0.0
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

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
    if len(valor) == 11: st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESP:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO:", f"input_curso_key_{s_al}"), ("PAGTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA:", f"f_data_{s_ge}")]
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        st.write("")
        _, c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 1.2, 0.2])
        c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento)
        c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento)
        c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento)
        if st.button("💾 SALVAR ALUNO", use_container_width=True):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]), "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                st.session_state.reset_aluno += 1; st.rerun()
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True)
            if st.button("📤 ENVIAR TUDO PARA SHEETS", use_container_width=True):
                try:
                    creds_info = st.secrets["connections"]["gsheets"]
                    client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                    ws.append_rows([[ "ATIVO", "MGA", "A DEFINIR", "SIM", "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]] for a in st.session_state.lista_previa])
                    st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO (AGGRID COMPLETO) ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    with cf4: 
        if st.button("🔄", key="btn_ref"): st.cache_data.clear(); st.rerun()
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False, na=False) | df_g['ID'].str.contains(bu, case=False, na=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]
        df_display = df_g.iloc[::-1].copy()
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_selection('single', use_checkbox=False)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(resizable=True, filter=True, sortable=True)
        gb.configure_column("ALUNO", pinned='left', width=250)
        grid_options = gb.build()
        col_t, col_e = st.columns([0.7, 0.3])
        with col_t: res = AgGrid(df_display, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED, theme='balham', height=650)
        with col_e:
            sel = res['selected_rows']
            if sel is not None and len(sel) > 0:
                aluno = sel[0] if isinstance(sel, list) else sel.iloc[0]
                st.markdown(f"### 📝 Editar: {aluno['ALUNO']}")
                with st.form("edit_f"):
                    n_st = st.selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if aluno['STATUS']=="ATIVO" else 1)
                    n_tu = st.text_input("TURMA", value=aluno['TURMA'])
                    n_pg = st.text_area("PAGAMENTO", value=aluno['PAGTO'], height=250)
                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        try:
                            creds_info = st.secrets["connections"]["gsheets"]
                            client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                            sh = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                            ids = sh.col_values(7); idx = ids.index(str(aluno['ID'])) + 1
                            sh.update_cell(idx, 1, n_st); sh.update_cell(idx, 3, n_tu.upper()); sh.update_cell(idx, 14, n_pg.upper())
                            st.success("Salvo!"); st.cache_data.clear(); st.rerun()
                        except: st.error("Erro ao salvar.")
            else: st.info("Clique em um aluno para editar.")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"
        df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            v_taxa, v_cartao, v_entrada = 0.0, 0.0, 0.0
            for linha in df_f['Pagamento'].tolist():
                if not linha: continue
                l_u = str(linha).upper()
                if "ALTERAÇÃO" in l_u or "ALTEROU PARA" in l_u:
                    match_alt = re.search(r'\((?:.*?PARA\s+)?(.*?)\)', l_u)
                    if match_alt: l_u = match_alt.group(1)
                t_n = re.findall(r'TAXA.*?(\d+)', l_u)
                for t in t_n:
                    try: v_taxa += float(t)
                    except: pass
                if "TAXA" in l_u and "PAGA" in l_u and not t_n: v_taxa += 50.0
                m_mult = re.findall(r'(\d+)\s*[X]\s*(?:R\$)?\s*([\d\.,]+)', l_u)
                if m_mult and ("CARTÃO" in l_u or "LINK" in l_u):
                    for q, v in m_mult:
                        try: v_cartao += int(q) * float(v.replace('.', '').replace(',', '.'))
                        except: pass
                else:
                    m_fixo = re.findall(r'(?:PAGO|R\$)\s*([\d\.]+,\d{2}|[\d\.]+)', l_u)
                    for val in m_fixo:
                        try:
                            vl = float(val.replace('.', '').replace(',', '.'))
                            if vl != 50.0:
                                if "CARTÃO" in l_u or "LINK" in l_u: v_cartao += vl
                                else: v_entrada += vl
                        except: pass
            total_final = v_taxa + v_cartao + v_entrada
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: st.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">TOTAL RECEBIDO</span><h2 style="font-size:22px">R${total_final:,.2f}</h2></div>', unsafe_allow_html=True)
            with c5:
                df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
                tm_b = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
                tm_c = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
                st.markdown(f'<div class="card-hud neon-purple"><span class="stat-label">TICKET MÉDIO</span><div style="font-size:18px; font-weight:bold; color:#e0e0e0;">BOL: R${tm_b:.0f}<br>CAR: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
            with c6:
                c_banc = len(df_f[df_f["Curso"].str.contains("BANCÁRIO", case=False, na=False)])
                c_agro = len(df_f[df_f["Curso"].str.contains("AGRO", case=False, na=False)])
                c_ing = len(df_f[df_f["Curso"].str.contains("INGLÊS", case=False, na=False)])
                c_tec = len(df_f[df_f["Curso"].str.contains("TECNOLOGIA|INFORMÁTICA", case=False, na=False)])
                st.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">POR ÁREA</span><div style="font-size:15px; text-align:left; color:#e0e0e0; line-height:1.4; padding-left:5px;">BANC: <b>{c_banc}</b> | AGRO: <b>{c_agro}</b><br>INGL: <b>{c_ing}</b> | TECN: <b>{c_tec}</b></div></div>', unsafe_allow_html=True)
            
            # --- CORREÇÃO DA SINTAXE DO GRÁFICO ---
            at_count = len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])
            can_count = len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])
            
            fig_st = go.Figure()
            fig_st.add_trace(go.Bar(
                y=["STATUS"], x=[at_count], orientation='h', 
                marker=dict(color='#2ecc71'), text=["ATIVOS"], textposition='inside'
            ))
            fig_st.add_trace(go.Bar(
                y=["STATUS"], x=[can_count], orientation='h', 
                marker=dict(color='#ff4b4b'), text=["CANCELADOS"], textposition='inside'
            ))
            fig_st.update_layout(
                barmode='stack', showlegend=False, height=50, margin=dict(t=5,b=5), 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            st.plotly_chart(fig_st, use_container_width=True)

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                df_city = df_f.copy(); df_city["Vendedor_L"] = df_city["Vendedor"].str.split(" - ").str[0].str.strip()
                top_cities = df_city['Cidade'].value_counts().head(5).index
                df_city_plot = pd.DataFrame([{"Cidade": c, "Qtd": len(df_city[df_city['Cidade']==c]), "Vendedores": ", ".join(df_city[df_city['Cidade']==c]['Vendedor_L'].unique())} for c in top_cities])
                st.plotly_chart(go.Figure(go.Bar(x=df_city_plot['Cidade'], y=df_city_plot['Qtd'], text=df_city_plot.apply(lambda r: f"<b>{r['Qtd']}</b>", axis=1), textposition='outside', marker=dict(color=df_city_plot['Qtd'], colorscale='Blues'))).update_layout(template="plotly_dark", title="📍 TOP CIDADES"), use_container_width=True)
            with col_g2:
                df_stats = df_f.copy(); df_stats["Vendedor"] = df_stats["Vendedor"].str.split(" - ").str[0].str.strip()
                df_v = df_stats["Vendedor"].value_counts().reset_index().head(5)
                st.plotly_chart(go.Figure(go.Scatter(x=df_v['Vendedor'], y=df_v['count'], mode='lines+markers+text', text=df_v['count'], textposition="top center", line=dict(color='#bc13fe'))).update_layout(template="plotly_dark", title="⚡ PERFORMANCE VENDAS"), use_container_width=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    if modo == "AUTOMÁTICO":
        df_m = safe_read()
        if not df_m.empty:
            try:
                col_f = df_m.columns[5]; df_m[col_f] = pd.to_datetime(df_m[col_f], dayfirst=True, errors='coerce')
                data_sel = st.date_input("Filtrar Cadastro:", value=date.today())
                df_filtrado = df_m[df_m[col_f].dt.date == data_sel]
                if not df_filtrado.empty:
                    cids = sorted(df_filtrado[df_m.columns[11]].unique()); sel_cids = st.multiselect("Cidades:", cids)
                    st.session_state.df_auto_ready = df_filtrado[df_filtrado[df_m.columns[11]].isin(sel_cids)]
                    st.info(f"{len(st.session_state.df_auto_ready)} encontrados.")
            except: st.error("Erro no processamento.")
    else:
        c1, c2 = st.columns(2)
        with c1: u_user = st.text_area("IDs", height=100, key="in_user"); u_cell = st.text_area("Celulares", height=100, key="in_cell"); u_city = st.text_area("Cidades", height=100, key="in_city"); u_pay = st.text_area("Pagamentos", height=100, key="in_pay")
        with c2: u_nome = st.text_area("Nomes", height=100, key="in_nome"); u_doc = st.text_area("Documentos", height=100, key="in_doc"); u_cour = st.text_area("Cursos", height=100, key="in_cour"); u_sell = st.text_area("Vendedores", height=100, key="in_sell")
        u_date = st.text_area("Datas", height=100, key="in_date")
    with st.expander("🛠️ CONFIGURAR TAGS", expanded=False):
        cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
        cols = st.columns(3); selected_tags = {}
        for i, curso in enumerate(cursos_tags):
            with cols[i % 3]:
                tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, [])
                last_sel = st.session_state.dados_tags.get("last_selection", {}).get(curso, "")
                idx_default = (tags_lista.index(last_sel) + 1) if last_sel in tags_lista else 0
                cur_tag = st.selectbox(curso, [""] + tags_lista, index=idx_default, key=f"sel_{curso}")
                if cur_tag != last_sel: st.session_state.dados_tags["last_selection"][curso] = cur_tag; salvar_tags(st.session_state.dados_tags)
                new_tag = st.text_input(f"Nova para {curso}", key=f"new_{i}").upper()
                if new_tag and new_tag not in tags_lista:
                    if curso not in st.session_state.dados_tags["tags"]: st.session_state.dados_tags["tags"][curso] = []
                    st.session_state.dados_tags["tags"][curso].append(new_tag); salvar_tags(st.session_state.dados_tags); st.rerun()
                selected_tags[curso] = (new_tag if new_tag else cur_tag).upper()
    if st.button("🚀 PROCESSAR DADOS", use_container_width=True):
        raw_list = []
        if modo == "MANUAL":
            l_ids, l_nomes, l_pays = u_user.strip().split('\n'), u_nome.strip().split('\n'), u_pay.strip().split('\n')
            l_cours, l_cells, l_docs = u_cour.strip().split('\n'), u_cell.strip().split('\n'), u_doc.strip().split('\n')
            l_citys, l_sells, l_dates = u_city.strip().split('\n'), u_sell.strip().split('\n'), u_date.strip().split('\n')
            for i in range(len(l_ids)):
                try: raw_list.append({"User": l_ids[i], "Nome": l_nomes[i], "Pay": l_pays[i], "Cour": l_cours[i], "Cell": l_cells[i], "Doc": l_docs[i], "City": l_citys[i], "Sell": l_sells[i], "Date": l_dates[i]})
                except: continue
        elif "df_auto_ready" in st.session_state:
            for _, r in st.session_state.df_auto_ready.iterrows(): raw_list.append({"User": r.iloc[6], "Nome": r.iloc[7], "Cell": r.iloc[9], "Doc": r.iloc[10], "City": r.iloc[11], "Cour": r.iloc[12], "Pay": r.iloc[13], "Sell": r.iloc[14], "Date": r.iloc[15]})
        if raw_list:
            processed = []
            for item in raw_list:
                c_orig, p_orig = str(item['Cour']).upper(), str(item['Pay']).upper()
                tags_f = [selected_tags[k] for k in cursos_tags if k in c_orig and selected_tags.get(k)]
                c_final = ",".join(tags_f).upper() if tags_f else c_orig
                p_final = "PENDENTE"; has_bol, has_car = "BOLETO" in p_orig, ("CARTÃO" in p_orig or "LINK" in p_orig)
                if (has_bol and not has_car): p_final = "BOLETO"
                elif (has_car and not has_bol): p_final = "CARTÃO"
                processed.append({"username": item['User'], "email2": f"{item['User']}@profissionalizaead.com.br", "name": str(item['Nome']).split(" ")[0].upper(), "lastname": " ".join(str(item['Nome']).split(" ")[1:]).upper(), "cellphone2": str(item['Cell']), "document": item['Doc'], "city2": item['City'], "courses": c_final, "payment": p_final, "observation": f"{c_final} | {c_orig} | {p_orig}".upper(), "ouro": "1" if "10 CURSOS" in c_orig else "0", "password": "futuro", "role": "1", "secretary": "MGA", "seller": item['Sell'], "contract_date": item['Date'], "active": "1"})
            st.session_state.df_final_processado = pd.DataFrame(processed)
    if st.session_state.df_final_processado is not None:
        df = st.session_state.df_final_processado; mask = df['payment'] == "PENDENTE"
        if mask.any():
            df_conf = df.loc[mask, ["username", "name", "observation"]].copy(); df_conf["Forma Final"] = "BOLETO"
            edited = st.data_editor(df_conf, column_config={"Forma Final": st.column_config.SelectboxColumn("Forma", options=["BOLETO", "CARTÃO"], required=True)}, hide_index=True, use_container_width=True)
            if st.button("✅ CONFIRMAR E GERAR EXCEL"):
                for _, row in edited.iterrows(): df.loc[df['username'] == row["username"], "payment"] = row["Forma Final"]
                st.session_state.df_final_processado = df; st.rerun()
        if not (st.session_state.df_final_processado['payment'] == "PENDENTE").any():
            output = BytesIO(); wb = Workbook(); ws = wb.active; ws.append(list(st.session_state.df_final_processado.columns))
            for r in st.session_state.df_final_processado.values.tolist(): ws.append([str(val) for val in r])
            wb.save(output); st.download_button("📥 BAIXAR EXCEL FINAL", output.getvalue(), f"ead_{date.today()}.xlsx", on_click=reset_campos_subir, use_container_width=True)
