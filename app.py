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
        except:
            return {}
    return {}

def salvar_tags(tags):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

if "tags_salvas" not in st.session_state:
    st.session_state.tags_salvas = carregar_tags()

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS ESTÉTICA HUD NEON & LAYOUT ---
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
    
    /* CADASTRO */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 55% !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    /* GERENCIAMENTO */
    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }
    .custom-table tr:hover { background-color: rgba(0, 242, 255, 0.1); }
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* SUBIR ALUNOS */
    .subir-label { color: #e0e6ed !important; font-size: 14px !important; margin-bottom: 2px !important; font-weight: bold; }
    .stTextArea textarea { background-color: white !important; color: black !important; text-transform: uppercase !important; border-radius: 0px !important; }
    .contador-label { color: #00f2ff !important; font-size: 10px !important; margin-top: -10px; margin-bottom: 10px; text-align: right; }
    .btn-salvar-planilha > div [data-testid="stButton"] button {
        background-color: #805dca !important; color: white !important; font-weight: bold !important; width: 100% !important; border-radius: 0px !important; height: 45px !important;
    }

    /* RELATÓRIO */
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

    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES ORIGINAIS DE CONTROLE ---
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

# --- ABA 1: CADASTRO (RESTAURADA 100%) ---
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
        if st.session_state.lista_previa: st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO (RESTAURADA 100%) ---
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
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]

        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            rows += f"<tr><td><span class='status-badge {sc}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in hd]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS (RESTAURADA 100%) ---
with tab_rel:
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            df_r.columns = [c.strip() for c in df_r.columns]; v_col = "Vendedor"
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
                    figp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=400); st.plotly_chart(figp, use_container_width=True)
                with colg2:
                    dfv = df_f[v_col].value_counts().reset_index().head(5)
                    figv = px.line(dfv, x=v_col, y='count', markers=True, text='count')
                    figv.update_traces(line_color='#00f2ff'); figv.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400); st.plotly_chart(figv, use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 4: SUBIR ALUNOS (SISTEMA DE PROCESSAMENTO) ---
with tab_subir:
    def contar_itens(texto):
        return len([i for i in texto.strip().split('\n') if i.strip()]) if texto else 0

    def reset_campos_subir():
        chaves = ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]
        for c in chaves: st.session_state[c] = ""
        st.session_state.processou = False
        st.session_state.finalizado = False

    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.markdown("<p class='subir-label'>Usuários</p>", unsafe_allow_html=True)
        u_user = st.text_area("User", height=80, label_visibility="collapsed", key="in_user")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_user)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Celular</p>", unsafe_allow_html=True)
        u_cell = st.text_area("Cel", height=80, label_visibility="collapsed", key="in_cell")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_cell)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Cidade</p>", unsafe_allow_html=True)
        u_city = st.text_area("Cid", height=80, label_visibility="collapsed", key="in_city")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_city)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Pagamento</p>", unsafe_allow_html=True)
        u_pay = st.text_area("Pay", height=80, label_visibility="collapsed", key="in_pay")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_pay)}</p>", unsafe_allow_html=True)
    with col_dir:
        st.markdown("<p class='subir-label'>Nome completo</p>", unsafe_allow_html=True)
        u_nome = st.text_area("Nome", height=80, label_visibility="collapsed", key="in_nome")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_nome)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Documento</p>", unsafe_allow_html=True)
        u_doc = st.text_area("Doc", height=80, label_visibility="collapsed", key="in_doc")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_doc)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Cursos</p>", unsafe_allow_html=True)
        u_cour = st.text_area("Cour", height=80, label_visibility="collapsed", key="in_cour")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_cour)}</p>", unsafe_allow_html=True)
        st.markdown("<p class='subir-label'>Vendedor</p>", unsafe_allow_html=True)
        u_sell = st.text_area("Sell", height=80, label_visibility="collapsed", key="in_sell")
        st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_sell)}</p>", unsafe_allow_html=True)

    st.markdown("<p class='subir-label'>Data contrato</p>", unsafe_allow_html=True)
    u_date = st.text_area("Date", height=80, label_visibility="collapsed", key="in_date")
    st.markdown(f"<p class='contador-label'>Itens: {contar_itens(u_date)}</p>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("<h4 style='color:#bc13fe; font-size:16px;'>CONFIGURAÇÃO DE TAGS</h4>", unsafe_allow_html=True)
    cursos_tag_list = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
    cols_tags = st.columns(5)
    selected_tags = {}
    for i, curso in enumerate(cursos_tag_list):
        with cols_tags[i % 5]:
            tag_opts = st.session_state.tags_salvas.get(curso, [])
            last_idx = 0
            last_val = st.session_state.get(f"last_tag_{curso}")
            if last_val in tag_opts: last_idx = tag_opts.index(last_val) + 1
            st.markdown(f"<p style='font-size:10px; margin-bottom:0px; font-weight:bold;'>{curso}</p>", unsafe_allow_html=True)
            current_t = st.selectbox(curso, options=[""] + tag_opts, index=last_idx, key=f"sel_{curso}", label_visibility="collapsed")
            new_t = st.text_input(f"New {curso}", key=f"nt_{curso}", label_visibility="collapsed", placeholder="Nova...").upper()
            final_t = (new_t if new_t else current_t).upper()
            if final_t: st.session_state[f"last_tag_{curso}"] = final_t
            selected_tags[curso] = final_t
            if st.button("🗑️", key=f"del_{curso}"):
                if current_t in st.session_state.tags_salvas.get(curso, []):
                    st.session_state.tags_salvas[curso].remove(current_t)
                    salvar_tags(st.session_state.tags_salvas); st.rerun()

    st.write("---")
    st.markdown('<div class="btn-salvar-planilha">', unsafe_allow_html=True)
    if st.button("Salvar planilha", use_container_width=True):
        if not os.path.exists(ARQUIVO_CIDADES): st.error("Arquivo cidades.xlsx não encontrado.")
        elif not u_user: st.error("Insira os dados.")
        else:
            wb_c = load_workbook(ARQUIVO_CIDADES); ws_c = wb_c.active
            cid_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]}
            l_u = u_user.strip().split('\n'); l_n = u_nome.strip().split('\n'); l_p = u_pay.strip().split('\n')
            l_co = u_cour.strip().split('\n'); l_ce = u_cell.strip().split('\n'); l_d = u_doc.strip().split('\n')
            l_ci = u_city.strip().split('\n'); l_s = u_sell.strip().split('\n'); l_dt = u_date.strip().split('\n')

            for k, v in selected_tags.items():
                if v and v not in st.session_state.tags_salvas.get(k, []):
                    if k not in st.session_state.tags_salvas: st.session_state.tags_salvas[k] = []
                    st.session_state.tags_salvas[k].append(v.upper())
            salvar_tags(st.session_state.tags_salvas)

            processed, pendentes = [], []
            for i in range(len(l_u)):
                try:
                    n_up = l_n[i].strip().upper()
                    fname = n_up.split(" ")[0]; lname = " ".join(n_up.split(" ")[1:]) if " " in n_up else ""
                    c_o = l_co[i].strip().upper(); p_o = l_p[i].strip().upper()
                    t_a = [selected_tags[k].upper() for k in cursos_tag_list if k in c_o and selected_tags.get(k)]
                    courses_col = ",".join(t_a).upper() if t_a else c_o.upper()
                    obs = f"{','.join(t_a) if t_a else 'SEM TAG'} | {c_o} | {p_o}".upper()
                    p_f = "BOLETO" if ("BOLETO" in p_o or "SEM FORMA" in p_o) else ("CARTÃO" if "BOLSA 100%" in p_o else p_o)
                    if "CARTÃO" in p_o: pendentes.append({"Index": i, "Aluno": n_up, "Orig": p_o, "Opção": "CARTÃO"})
                    processed.append({
                        "username": l_u[i], "email2": f"{l_u[i]}@profissionalizaead.com.br", "name": fname, "lastname": lname,
                        "cellphone2": l_ce[i], "document": l_d[i], "city2": cid_map.get(l_ci[i].strip().upper(), l_ci[i]),
                        "courses": courses_col, "payment": p_f, "observation": obs, "ouro": "1" if "+ 10" in obs else "0",
                        "password": "futuro", "role": "1", "secretary": "MGA", "seller": l_s[i], "contract_date": l_dt[i], "active": "1"
                    })
                except: continue
            st.session_state.dados_brutos, st.session_state.pendentes, st.session_state.processou = processed, pendentes, True

    if st.session_state.get("processou"):
        if st.session_state.pendentes:
            st.warning("⚠️ Confirme os pagamentos em CARTÃO:")
            ed_df = st.data_editor(pd.DataFrame(st.session_state.pendentes), column_config={"Opção": st.column_config.SelectboxColumn("Opção", options=["CARTÃO", "BOLETO"], required=True)}, disabled=["Index", "Aluno", "Orig"], hide_index=True, key="ed_pag_final")
            if st.button("Gerar Planilha Final"):
                for _, row in ed_df.iterrows(): st.session_state.dados_brutos[row["Index"]]["payment"] = row["Opção"]
                out = BytesIO(); wb = Workbook(); ws = wb.active; cols = ["username", "email2", "name", "lastname", "cellphone2", "document", "city2", "courses", "payment", "observation", "ouro", "password", "role", "secretary", "seller", "contract_date", "active"]
                ws.append(cols); [ws.append([d[c] for c in cols]) for d in st.session_state.dados_brutos]; wb.save(out)
                st.session_state.excel_pronto, st.session_state.finalizado = out.getvalue(), True
        
        if st.session_state.get("finalizado") or not st.session_state.pendentes:
            ex_data = st.session_state.get("excel_pronto")
            if not ex_data:
                out = BytesIO(); wb = Workbook(); ws = wb.active; cols = ["username", "email2", "name", "lastname", "cellphone2", "document", "city2", "courses", "payment", "observation", "ouro", "password", "role", "secretary", "seller", "contract_date", "active"]
                ws.append(cols); [ws.append([d[c] for c in cols]) for d in st.session_state.dados_brutos]; wb.save(out)
                ex_data = out.getvalue()
            st.download_button("📥 Baixar Excel", ex_data, f"ead_final_{date.today()}.xlsx", on_click=reset_campos_subir)
    st.markdown('</div>', unsafe_allow_html=True)
