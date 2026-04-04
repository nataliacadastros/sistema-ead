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
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- ARQUIVOS E PERSISTÊNCIA ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

def carregar_tags():
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_tags(tags):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

if "tags_salvas" not in st.session_state:
    st.session_state.tags_salvas = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    .main .block-container { padding-top: 45px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 55% !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }
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

    .subir-label { color: #e0e6ed !important; font-size: 14px !important; margin-bottom: 2px !important; font-weight: bold; }
    .stTextArea textarea { background-color: white !important; color: black !important; text-transform: uppercase !important; border-radius: 0px !important; }
    .contador-label { color: #00f2ff !important; font-size: 10px !important; margin-top: -10px; margin-bottom: 10px; text-align: right; }
    .btn-salvar-planilha > div [data-testid="stButton"] button { background-color: #805dca !important; color: white !important; font-weight: bold !important; width: 100% !important; border-radius: 0px !important; height: 45px !important; }

    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "processou" not in st.session_state: st.session_state.processou = False
if "finalizado" not in st.session_state: st.session_state.finalizado = False
if "excel_pronto" not in st.session_state: st.session_state.excel_pronto = None

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÕES ---
def reset_campos_subir():
    chaves = ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]
    for c in chaves: 
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.processou = False
    st.session_state.finalizado = False
    st.session_state.excel_pronto = None

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

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0

def extrair_valor_geral(texto):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        c_fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
             ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
             ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
             ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in c_fields:
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
        if st.session_state.lista_previa: st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

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
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]
        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            rows += f"<tr><td><span class='status-badge {sc}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in df_g.columns]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro no Gerenciamento")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            df_r.columns = [c.strip() for c in df_r.columns]
            v_col = "Vendedor"
            if v_col in df_r.columns: df_r[v_col] = df_r[v_col].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
            dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            iv = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
                df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido); df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="card-hud neon-red"><small>Cancelados</small><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c5:
                    tm_b = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
                    tm_c = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
                    st.markdown(f'<div class="card-hud neon-purple"><small>Ticket Médio</small><div style="font-size:10px">Bol: R${tm_b:.0f} | Car: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
                with c6: st.markdown(f'<div class="card-hud neon-blue"><small>Top</small><h2 style="font-size:14px">{df_f[v_col].value_counts().idxmax() if not df_f.empty else "N/A"}</h2></div>', unsafe_allow_html=True)
                st.write("---")
                df_cv = df_f['Cidade'].value_counts().head(4)
                if not df_cv.empty:
                    st.markdown("<small style='color:#00f2ff'>▸ GEOLOCATION ANALYTICS</small>", unsafe_allow_html=True)
                    t_c = df_cv.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                    s_html = "".join([f'<div class="hud-segment" style="width:{(q/t_c)*100}%; background:{cores[i%4]};"><div class="hud-label" style="color:{cores[i%4]};">{q}</div><div class="hud-city-name" style="color:{cores[i%4]};">{n}</div></div>' for i, (n, q) in enumerate(df_cv.items())])
                    st.markdown(f'<div class="hud-bar-container">{s_html}</div>', unsafe_allow_html=True)
                colg1, colg2 = st.columns(2)
                with colg1:
                    figp = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b']))])
                    figp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400); st.plotly_chart(figp, use_container_width=True)
                with colg2:
                    dfv = df_f[v_col].value_counts().reset_index().head(5)
                    figv = px.line(dfv, x=v_col, y='count', markers=True, text='count')
                    figv.update_traces(line_color='#00f2ff'); figv.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400); st.plotly_chart(figv, use_container_width=True)
    except Exception as e: st.error("Erro nos Relatórios")

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 MODO DE IMPORTAÇÃO")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True, label_visibility="collapsed")
    st.write("---")

    df_mestre = None # Inicializa para evitar NameError
    cidades_sel = []

    if modo == "MANUAL":
        def contar_itens(texto): return len([i for i in texto.strip().split('\n') if i.strip()]) if texto else 0
        col_esq, col_dir = st.columns(2)
        with col_esq:
            u_user = st.text_area("Usuários", height=80, key="in_user")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_user)}</p>", unsafe_allow_html=True)
            u_cell = st.text_area("Celular", height=80, key="in_cell")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_cell)}</p>", unsafe_allow_html=True)
            u_city = st.text_area("Cidade", height=80, key="in_city")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_city)}</p>", unsafe_allow_html=True)
            u_pay = st.text_area("Pagamento", height=80, key="in_pay")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_pay)}</p>", unsafe_allow_html=True)
        with col_dir:
            u_nome = st.text_area("Nome completo", height=80, key="in_nome")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_nome)}</p>", unsafe_allow_html=True)
            u_doc = st.text_area("Documento", height=80, key="in_doc")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_doc)}</p>", unsafe_allow_html=True)
            u_cour = st.text_area("Cursos", height=80, key="in_cour")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_cour)}</p>", unsafe_allow_html=True)
            u_sell = st.text_area("Vendedor", height=80, key="in_sell")
            st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_sell)}</p>", unsafe_allow_html=True)
        u_date = st.text_area("Data contrato", height=80, key="in_date")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_date)}</p>", unsafe_allow_html=True)

    else:
        st.markdown("<h4 style='color:#00f2ff'>FILTRAR POR DATA</h4>")
        try:
            # TTL=300 (5 min) evita o erro 429 de cota excedida
            df_mestre = conn.read(ttl=300).dropna(how='all')
            df_mestre.columns = [c.strip().upper() for c in df_mestre.columns]
            col_data = next((c for c in df_mestre.columns if 'DATA MAT' in c or 'DT_MAT' in c), None)
            col_cid = next((c for c in df_mestre.columns if 'CIDADE' in c), None)

            if col_data and col_cid:
                df_mestre[col_data] = pd.to_datetime(df_mestre[col_data], dayfirst=True, errors='coerce')
                data_sel = st.date_input("Dia:", value=date.today(), format="DD/MM/YYYY")
                df_f_auto = df_mestre[df_mestre[col_data].dt.date == data_sel]
                if not df_f_auto.empty:
                    cids_l = sorted(df_f_auto[col_cid].unique())
                    cidades_sel = st.multiselect("Cidades:", cids_l, key="auto_cids_sel")
                    st.info(f"{len(df_f_auto[df_f_auto[col_cid].isin(cidades_sel)])} alunos encontrados.")
                else: st.warning("Nenhum cadastro nesta data.")
        except Exception: st.error("Erro de Cota (Google): Aguarde 1 minuto.")

    # --- TAGS ---
    st.write("---")
    st.markdown("<h4 style='color:#bc13fe; font-size:16px;'>CONFIGURAÇÃO DE TAGS</h4>", unsafe_allow_html=True)
    cursos_tag_list = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
    cols_tags = st.columns(5)
    selected_tags = {}
    for i, curso in enumerate(cursos_tag_list):
        with cols_tags[i % 5]:
            tag_opts = st.session_state.tags_salvas.get(curso, [])
            last_val = st.session_state.get(f"last_tag_{curso}")
            idx = tag_opts.index(last_val) + 1 if last_val in tag_opts else 0
            current_t = st.selectbox(curso, options=[""] + tag_opts, index=idx, key=f"sel_{curso}")
            new_t = st.text_input(f"New {curso}", key=f"nt_{curso}", placeholder="Nova...").upper()
            final_t = (new_t if new_t else current_t).upper()
            selected_tags[curso] = final_t
            if final_t: st.session_state[f"last_tag_{curso}"] = final_t

    # --- PROCESSAMENTO FINAL ---
    st.write("---")
    if st.button("🚀 PROCESSAR PLANILHA", use_container_width=True):
        if not os.path.exists(ARQUIVO_CIDADES): st.error("cidades.xlsx ausente.")
        else:
            wb_c = load_workbook(ARQUIVO_CIDADES); ws_c = wb_c.active
            cid_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]}
            for k, v in selected_tags.items():
                if v and v not in st.session_state.tags_salvas.get(k, []):
                    if k not in st.session_state.tags_salvas: st.session_state.tags_salvas[k] = []
                    st.session_state.tags_salvas[k].append(v); salvar_tags(st.session_state.tags_salvas)

            raw = []
            if modo == "MANUAL":
                l_u = u_user.strip().split('\n'); l_n = u_nome.strip().split('\n'); l_p = u_pay.strip().split('\n')
                for i in range(len(l_u)):
                    try: raw.append({"User": l_u[i], "Nome": l_n[i], "Pay": l_p[i], "Cour": u_cour.strip().split('\n')[i], "Cell": u_cell.strip().split('\n')[i], "Doc": u_doc.strip().split('\n')[i], "City": u_city.strip().split('\n')[i], "Sell": u_sell.strip().split('\n')[i], "Date": u_date.strip().split('\n')[i]})
                    except: continue
            elif df_mestre is not None:
                c_id = next((c for c in df_mestre.columns if 'ID' in c), 'ID')
                c_alu = next((c for c in df_mestre.columns if 'ALUNO' in c), 'ALUNO')
                c_pag = next((c for c in df_mestre.columns if 'PAGTO' in c or 'PAGAMENTO' in c), 'PAGTO')
                c_cur = next((c for c in df_mestre.columns if 'CURSO' in c), 'CURSO')
                c_tel = next((c for c in df_mestre.columns if 'TEL' in c), 'TEL_ALU')
                c_doc = next((c for c in df_mestre.columns if 'CPF' in c), 'CPF')
                c_ven = next((c for c in df_mestre.columns if 'VEND' in c), 'VENDEDOR')
                c_cid = next((c for c in df_mestre.columns if 'CIDADE' in c), 'CIDADE')
                c_dat = next((c for c in df_mestre.columns if 'DATA MAT' in c or 'DT_MAT' in c), 'DT_MAT')
                df_final = df_f_auto[df_f_auto[c_cid].isin(cidades_sel)]
                for _, r in df_final.iterrows(): raw.append({"User": r[c_id], "Nome": r[c_alu], "Pay": r[c_pag], "Cour": r[c_cur], "Cell": r[c_tel], "Doc": r[c_doc], "City": r[c_cid], "Sell": r[c_ven], "Date": r[c_dat]})

            processed, pends = [], []
            for i, item in enumerate(raw):
                n_up = str(item['Nome']).upper().strip(); c_o = str(item['Cour']).upper().strip(); p_o = str(item['Pay']).upper().strip()
                t_a = [selected_tags[k] for k in cursos_tag_list if k in c_o and selected_tags.get(k)]
                course_f = ",".join(t_a).upper() if t_a else c_o
                p_f = "BOLETO" if ("BOLETO" in p_o or "SEM FORMA" in p_o) else ("CARTÃO" if "BOLSA 100%" in p_o else p_o)
                if "CARTÃO" in p_o: pends.append({"Index": i, "Aluno": n_up, "Orig": p_o, "Opção": "CARTÃO"})
                processed.append({"username": item['User'], "email2": f"{item['User']}@profissionalizaead.com.br", "name": n_up.split(" ")[0], "lastname": " ".join(n_up.split(" ")[1:]) if " " in n_up else "", "cellphone2": item['Cell'], "document": item['Doc'], "city2": cid_map.get(str(item['City']).upper(), item['City']), "courses": course_f, "payment": p_f, "observation": f"{course_f} | {p_o}".upper(), "ouro": "1" if "10" in course_f else "0", "password": "futuro", "role": "1", "secretary": "MGA", "seller": item['Sell'], "contract_date": item['Date'], "active": "1"})
            st.session_state.dados_brutos, st.session_state.pendentes, st.session_state.processou = processed, pends, True

    if st.session_state.get("processou"):
        if st.session_state.pendentes:
            st.warning("Confirme pagamentos CARTÃO:")
            ed = st.data_editor(pd.DataFrame(st.session_state.pendentes), column_config={"Opção": st.column_config.SelectboxColumn("Opção", options=["CARTÃO", "BOLETO"])}, hide_index=True)
            if st.button("Gerar Excel Final"):
                for _, r in ed.iterrows(): st.session_state.dados_brutos[r["Index"]]["payment"] = r["Opção"]
                out = BytesIO(); wb = Workbook(); ws = wb.active; cols = list(st.session_state.dados_brutos[0].keys()); ws.append(cols)
                for d in st.session_state.dados_brutos: ws.append([d[c] for c in cols])
                wb.save(out); st.session_state.excel_pronto, st.session_state.finalizado = out.getvalue(), True
        
        if st.session_state.get("finalizado") or not st.session_state.pendentes:
            data = st.session_state.excel_pronto if st.session_state.excel_pronto else None
            if not data:
                out = BytesIO(); wb = Workbook(); ws = wb.active; cols = list(st.session_state.dados_brutos[0].keys()); ws.append(cols)
                for d in st.session_state.dados_brutos: ws.append([d[c] for c in cols])
                wb.save(out); data = out.getvalue()
            st.download_button("📥 Baixar Excel", data, f"ead_{date.today()}.xlsx", on_click=reset_campos_subir)
