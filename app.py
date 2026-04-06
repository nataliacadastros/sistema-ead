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
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict) and "tags" in conteudo: return conteudo
                elif isinstance(conteudo, dict): return {"tags": conteudo, "last_selection": {}}
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
    
    div.stButton > button {
        background-color: #00f2ff !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }

    .stTextArea textarea { background-color: white !important; color: black !important; text-transform: uppercase !important; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_gsheets_client():
    creds_info = st.secrets["connections"]["gsheets"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds), creds_info["spreadsheet"]

def safe_read():
    try: return conn.read(ttl="5s").dropna(how='all')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES AUXILIARES ---
def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0

def extrair_valor_geral(texto):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def transformar_curso(chave):
    entrada = st.session_state[chave].strip()
    if not (entrada and re.search(r'(\d+)$', entrada)): return
    match = re.search(r'(\d+)$', entrada)
    codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
    if nome:
        base = entrada[:match.start()].strip().rstrip('+').strip()
        st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper()

# --- MODAIS DE EDIÇÃO ---
@st.dialog("📝 EDITAR ALUNO")
def modal_editar_individual(aluno):
    new_data = {}
    cols = st.columns(2)
    campos = [('STATUS', ['ATIVO', 'CANCELADO']), ('UNID.', ['MGA', 'A DEFINIR']), ('TURMA', None), ('10C', ['SIM', 'NÃO']), ('ING', ['SIM', 'NÃO']), ('ALUNO', None), ('TEL_RESP', None), ('TEL_ALU', None), ('CPF', None), ('CIDADE', None), ('CURSO', None), ('PAGTO', None), ('VEND.', None), ('DT_MAT', None)]
    for i, (l, opt) in enumerate(campos):
        with cols[i % 2]:
            if opt: new_data[l] = st.selectbox(l, opt, index=opt.index(aluno[l]) if aluno[l] in opt else 0)
            else: new_data[l] = st.text_input(l, value=str(aluno[l])).upper()
    if st.button("💾 SALVAR", use_container_width=True):
        client, sheet_id = get_gsheets_client(); ws = client.open_by_url(sheet_id).get_worksheet(0)
        cell = ws.find(aluno['ID'], in_column=7)
        if cell:
            ws.update(f'A{cell.row}:P{cell.row}', [[new_data['STATUS'], new_data['UNID.'], new_data['TURMA'], new_data['10C'], new_data['ING'], aluno['DT_CAD'], aluno['ID'], new_data['ALUNO'], new_data['TEL_RESP'], new_data['TEL_ALU'], new_data['CPF'], new_data['CIDADE'], new_data['CURSO'], new_data['PAGTO'], new_data['VEND.'], new_data['DT_MAT']]])
            st.success("Salvo!"); st.cache_data.clear(); st.rerun()

@st.dialog("⚡ EDIÇÃO EM LOTE")
def modal_editar_lote(selecionados_ids):
    st.write(f"Editando {len(selecionados_ids)} alunos.")
    c1, c2, c3 = st.columns(3)
    b_status = c1.selectbox("Status", ["", "ATIVO", "CANCELADO"])
    b_unid = c2.selectbox("Unidade", ["", "MGA", "A DEFINIR"])
    b_turma = c3.text_input("Turma").upper()
    b_10c = c1.selectbox("10C", ["", "SIM", "NÃO"])
    b_ing = c2.selectbox("ING", ["", "SIM", "NÃO"])
    if st.button("🚀 APLICAR EM TODOS", use_container_width=True):
        client, sheet_id = get_gsheets_client(); ws = client.open_by_url(sheet_id).get_worksheet(0)
        for aid in selecionados_ids:
            cell = ws.find(aid, in_column=7)
            if cell:
                if b_status: ws.update_cell(cell.row, 1, b_status)
                if b_unid: ws.update_cell(cell.row, 2, b_unid)
                if b_turma: ws.update_cell(cell.row, 3, b_turma)
                if b_10c: ws.update_cell(cell.row, 4, b_10c)
                if b_ing: ws.update_cell(cell.row, 5, b_ing)
        st.success("Lote Processado!"); st.cache_data.clear(); st.rerun()

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"), ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"), ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"), ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in fields:
            cl, ci = st.columns([1.5, 3.5]); cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        st.write("")
        if st.button("💾 SALVAR ALUNO", use_container_width=True):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                st.session_state.reset_aluno += 1; st.rerun()
        if st.button("📤 ENVIAR PLANILHA", use_container_width=True):
            if st.session_state.lista_previa:
                client, sheet_id = get_gsheets_client(); ws = client.open_by_url(sheet_id).get_worksheet(0); d_f = []
                for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
        if st.session_state.lista_previa: st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]

        # Ações de Seleção e Lote
        c_lote, c_exp = st.columns([2, 1])
        selecionados = []
        with c_lote:
            # Botão de Lote só aparece se houver checkboxes ativos no código abaixo
            pass

        rows_html = ""
        for i, r in df_g.iloc[::-1].iterrows():
            # Criamos uma chave única para cada checkbox e botão
            sc = "status-badge status-ativo" if r['STATUS'] == "ATIVO" else "status-badge status-cancelado"
            check_key = f"chk_{r['ID']}"
            btn_key = f"btn_ed_{r['ID']}"
            
            # Construção manual da linha para manter o visual original
            # Para o checkbox e botão funcionarem dentro da tabela original, 
            # usaremos colunas Streamlit para simular a tabela, ou botões flutuantes.
            # Mas para manter o DESIGN ORIGINAL 100%, vamos usar o layout de colunas do Streamlit simulando a tabela.
            
        # Re-renderização da tabela com suporte a botões
        cols_size = [0.3, 0.4, 0.6, 0.5, 0.6, 0.3, 0.3, 0.6, 1, 1.5, 1, 1, 1, 1.5, 2, 1, 1]
        st.markdown('<div class="custom-table-wrapper"><table class="custom-table"><thead><tr><th>SEL</th><th>EDIT</th><th>STATUS</th><th>UNID.</th><th>TURMA</th><th>10C</th><th>ING</th><th>DT_CAD</th><th>ID</th><th>ALUNO</th><th>TEL_RESP</th><th>TEL_ALU</th><th>CPF</th><th>CIDADE</th><th>CURSO</th><th>PAGTO</th><th>VEND.</th><th>DT_MAT</th></tr></thead></table></div>', unsafe_allow_html=True)
        
        ids_lote = []
        for i, r in df_g.iloc[::-1].iterrows():
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14, c15, c16, c17, c18 = st.columns([0.2, 0.3, 0.6, 0.4, 0.5, 0.3, 0.3, 0.5, 0.6, 1.5, 0.8, 0.8, 0.8, 0.8, 1.5, 1.5, 0.8, 0.7])
            if c1.checkbox("", key=f"sel_{r['ID']}"): ids_lote.append(r['ID'])
            if c2.button("📝", key=f"ed_{r['ID']}"): modal_editar_individual(r.to_dict())
            
            # Cores e Status
            badge = f'<span class="status-badge {"status-ativo" if r["STATUS"]=="ATIVO" else "status-cancelado"}">{r["STATUS"]}</span>'
            c3.markdown(badge, unsafe_allow_html=True)
            c4.write(r['UNID.'])
            c5.write(r['TURMA'])
            c6.write(r['10C'])
            c7.write(r['ING'])
            c8.write(r['DT_CAD'])
            c9.markdown(f"<span style='color:#00f2ff; font-weight:bold;'>{r['ID']}</span>", unsafe_allow_html=True)
            c10.markdown(f"<span style='color:#00f2ff; font-weight:bold;'>{r['ALUNO']}</span>", unsafe_allow_html=True)
            c11.write(r['TEL_RESP'])
            c12.write(r['TEL_ALU'])
            c13.write(r['CPF'])
            c14.write(r['CIDADE'])
            c15.write(r['CURSO'])
            c16.write(r['PAGTO'])
            c17.write(r['VEND.'])
            c18.write(r['DT_MAT'])
            st.markdown("<hr style='margin:2px; border:0.1px solid #1f295a'>", unsafe_allow_html=True)

        st.write("")
        if ids_lote:
            if st.button(f"⚡ EDITAR {len(ids_lote)} SELECIONADOS EM LOTE", use_container_width=True):
                modal_editar_lote(ids_lote)

        # Download
        out = BytesIO(); wb = Workbook(); ws_ex = wb.active; ws_ex.append(list(df_g.columns))
        for r in df_g.values.tolist(): ws_ex.append(r)
        wb.save(out)
        st.download_button("📥 BAIXAR EXCEL FILTRADO", out.getvalue(), "gerenciamento.xlsx", use_container_width=True)

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido); df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="card-hud neon-red"><small>Cancelados</small><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            tm_b = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
            tm_c = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
            c5.markdown(f'<div class="card-hud neon-purple"><small>Ticket Médio</small><div style="font-size:10px">Bol: R${tm_b:.0f} | Car: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
            c6.markdown(f'<div class="card-hud neon-blue"><small>Top</small><h2 style="font-size:14px">{df_f["Vendedor"].value_counts().idxmax() if not df_f.empty else "N/A"}</h2></div>', unsafe_allow_html=True)
            st.write("---")
            df_cv = df_f['Cidade'].value_counts().head(4)
            if not df_cv.empty:
                t_c = df_cv.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                s_html = "".join([f'<div class="hud-segment" style="width:{(q/t_c)*100}%; background:{cores[i%4]};"><div class="hud-label" style="color:{cores[i%4]};">{q}</div><div class="hud-city-name" style="color:{cores[i%4]};">{n}</div></div>' for i, (n, q) in enumerate(df_cv.items())])
                st.markdown(f'<div class="hud-bar-container">{s_html}</div>', unsafe_allow_html=True)
            g1, g2 = st.columns(2)
            with g1:
                figp = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b']))])
                figp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400); st.plotly_chart(figp, use_container_width=True)
            with g2:
                dfv = df_f["Vendedor"].value_counts().reset_index().head(5)
                figv = px.line(dfv, x='Vendedor', y='count', markers=True, text='count')
                figv.update_traces(line_color='#00f2ff'); figv.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400); st.plotly_chart(figv, use_container_width=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    if modo == "AUTOMÁTICO":
        df_m = safe_read()
        if not df_m.empty:
            col_f = df_m.columns[5]
            df_m[col_f] = pd.to_datetime(df_m[col_f], dayfirst=True, errors='coerce')
            data_sel = st.date_input("Filtrar Cadastro (Coluna F):", value=date.today())
            df_filtrado = df_m[df_m[col_f].dt.date == data_sel]
            if not df_filtrado.empty:
                sel_cids = st.multiselect("Cidades:", sorted(df_filtrado[df_m.columns[11]].unique()))
                st.session_state.df_auto_ready = df_filtrado[df_filtrado[df_m.columns[11]].isin(sel_cids)]
                st.info(f"{len(st.session_state.df_auto_ready)} alunos encontrados.")
    else:
        c1, c2 = st.columns(2); u_user = c1.text_area("IDs", height=100, key="in_user"); u_cell = c1.text_area("Celulares", height=100, key="in_cell"); u_city = c1.text_area("Cidades", height=100, key="in_city"); u_pay = c1.text_area("Pagamentos", height=100, key="in_pay"); u_nome = c2.text_area("Nomes", height=100, key="in_nome"); u_doc = c2.text_area("Documentos", height=100, key="in_doc"); u_cour = c2.text_area("Cursos", height=100, key="in_cour"); u_sell = c2.text_area("Vendedores", height=100, key="in_sell"); u_date = st.text_area("Datas", height=100, key="in_date")

    with st.expander("🛠️ CONFIGURAR TAGS", expanded=False):
        cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
        cols = st.columns(3); selected_tags = {}
        for i, curso in enumerate(cursos_tags):
            with cols[i % 3]:
                st.markdown(f"<p style='font-size:10px; margin-bottom:2px; color:#00f2ff; font-weight:bold;'>{curso}</p>", unsafe_allow_html=True)
                tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, [])
                last_sel = st.session_state.dados_tags.get("last_selection", {}).get(curso, "")
                idx_default = (tags_lista.index(last_sel) + 1) if last_sel in tags_lista else 0
                c_sel, c_del = st.columns([0.4, 0.6]); cur_tag = c_sel.selectbox("", [""] + tags_lista, index=idx_default, key=f"sel_{curso}", label_visibility="collapsed")
                if cur_tag != last_sel: st.session_state.dados_tags["last_selection"][curso] = cur_tag; salvar_tags(st.session_state.dados_tags)
                if c_del.button("🗑️", key=f"del_{curso}"):
                    if cur_tag and cur_tag in st.session_state.dados_tags["tags"][curso]:
                        st.session_state.dados_tags["tags"][curso].remove(cur_tag); st.session_state.dados_tags["last_selection"][curso] = ""; salvar_tags(st.session_state.dados_tags); st.rerun()
                c_new, _ = st.columns([0.4, 0.6]); new_tag = c_new.text_input("", placeholder="Nova...", key=f"new_{i}", label_visibility="collapsed").upper()
                if new_tag and new_tag not in tags_lista:
                    if "tags" not in st.session_state.dados_tags: st.session_state.dados_tags["tags"] = {}
                    if curso not in st.session_state.dados_tags["tags"]: st.session_state.dados_tags["tags"][curso] = []
                    st.session_state.dados_tags["tags"][curso].append(new_tag); st.session_state.dados_tags["last_selection"][curso] = new_tag; salvar_tags(st.session_state.dados_tags); st.rerun()
                selected_tags[curso] = (new_tag if new_tag else cur_tag).upper()

    if st.button("🚀 PROCESSAR DADOS", use_container_width=True):
        raw_list = []
        if modo == "MANUAL":
            l_ids = u_user.strip().split('\n')
            for i in range(len(l_ids)):
                try: raw_list.append({"User": l_ids[i], "Nome": u_nome.strip().split('\n')[i], "Pay": u_pay.strip().split('\n')[i], "Cour": u_cour.strip().split('\n')[i], "Cell": u_cell.strip().split('\n')[i], "Doc": u_doc.strip().split('\n')[i], "City": u_city.strip().split('\n')[i], "Sell": u_sell.strip().split('\n')[i], "Date": u_date.strip().split('\n')[i]})
                except: continue
        elif "df_auto_ready" in st.session_state and st.session_state.df_auto_ready is not None:
            for _, r in st.session_state.df_auto_ready.iterrows(): raw_list.append({"User": r.iloc[6], "Nome": r.iloc[7], "Cell": r.iloc[9], "Doc": r.iloc[10], "City": r.iloc[11], "Cour": r.iloc[12], "Pay": r.iloc[13], "Sell": r.iloc[14], "Date": r.iloc[15]})
        if raw_list:
            wb_c = load_workbook(ARQUIVO_CIDADES); ws_c = wb_c.active; c_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]}
            processed = []
            for item in raw_list:
                c_orig = str(item['Cour']).upper(); p_orig = str(item['Pay']).upper(); tags_f = [selected_tags[k] for k in cursos_tags if k in c_orig and selected_tags.get(k)]; c_final = ",".join(tags_f).upper() if tags_f else c_orig
                p_final = "PENDENTE"; has_bol = "BOLETO" in p_orig; has_car = "CARTÃO" in p_orig or "LINK" in p_orig
                if (has_bol and not has_car): p_final = "BOLETO"
                elif (has_car and not has_bol): p_final = "CARTÃO"
                obs_f = f"{c_final} | {c_orig} | {p_orig}".upper()
                processed.append({"username": item['User'], "email2": f"{item['User']}@profissionalizaead.com.br", "name": str(item['Nome']).split(" ")[0].upper(), "lastname": " ".join(str(item['Nome']).split(" ")[1:]).upper(), "cellphone2": item['Cell'], "document": item['Doc'], "city2": c_map.get(str(item['City']).upper(), item['City']), "courses": c_final, "payment": p_final, "observation": obs_f, "ouro": "1" if "10 CURSOS" in obs_f else "0", "password": "futuro", "role": "1", "secretary": "MGA", "seller": item['Sell'], "contract_date": item['Date'], "active": "1"})
            st.session_state.df_final_processado = pd.DataFrame(processed)

    if st.session_state.df_final_processado is not None:
        df = st.session_state.df_final_processado
        mask = df['payment'] == "PENDENTE"
        if mask.any():
            st.warning("⚠️ Confirmação necessária:"); df_conf = df.loc[mask, ["username", "name", "observation"]].copy(); df_conf.columns = ["ID", "Nome", "Texto Original"]; df_conf["Forma Final"] = "BOLETO"
            edited = st.data_editor(df_conf, column_config={"Forma Final": st.column_config.SelectboxColumn("Forma", options=["BOLETO", "CARTÃO"], required=True)}, disabled=["ID", "Nome", "Texto Original"], hide_index=True, use_container_width=True, key="pag_editor")
            if st.button("✅ CONFIRMAR E GERAR EXCEL"):
                for _, row in edited.iterrows(): df.loc[df['username'] == row["ID"], "payment"] = row["Forma Final"]
                st.session_state.df_final_processado = df; st.rerun()
        if not (st.session_state.df_final_processado['payment'] == "PENDENTE").any():
            output = BytesIO(); wb = Workbook(); ws = wb.active; ws.append(list(st.session_state.df_final_processado.columns))
            for r in st.session_state.df_final_processado.values.tolist(): ws.append(r)
            wb.save(output)
            st.download_button("📥 BAIXAR EXCEL FINAL", output.getvalue(), f"ead_{date.today()}.xlsx", on_click=reset_campos_subir, use_container_width=True)
