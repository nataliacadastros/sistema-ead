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
        width: 100%;
        max-height: 600px; 
        overflow: auto !important;
        background-color: #121629;
        border: 2px solid #1f295a;
        border-radius: 10px;
        margin-top: 15px;
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

    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}

    /* Estilo do botão de ID invisível na tabela */
    .id-btn-style button {
        background: none !important;
        border: 1px solid #00f2ff !important;
        color: #00f2ff !important;
        padding: 2px 8px !important;
        height: auto !important;
        font-size: 11px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES DE CONTROLE ---
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

# --- JANELA DE EDIÇÃO (MODAL) ---
@st.dialog("EDITAR ALUNO", width="large")
def editar_aluno_dialog(index, dados_atuais, colunas):
    st.markdown(f"### ID: {dados_atuais['ID']}")
    
    # Backup para desfazer
    if "original_data" not in st.session_state:
        st.session_state.original_data = dados_atuais.copy()

    col_undo, _ = st.columns([0.1, 0.9])
    if col_undo.button("↩️", help="Desfazer alterações"):
        for k, v in st.session_state.original_data.items():
            st.session_state[f"edit_{k}"] = str(v)
        st.rerun()

    novos_dados = {}
    c1, c2 = st.columns(2)
    for i, col in enumerate(colunas):
        target = c1 if i % 2 == 0 else c2
        key = f"edit_{col}"
        if key not in st.session_state:
            st.session_state[key] = str(dados_atuais[col])
        novos_dados[col] = target.text_input(col, key=key)

    if st.button("💾 SALVAR ALTERAÇÕES"):
        try:
            creds = st.secrets["connections"]["gsheets"]
            client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
            ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
            
            row_num = index + 2  # +2 por causa do cabeçalho
            ws.update(f'A{row_num}:P{row_num}', [[novos_dados[c] for c in colunas]])
            
            st.success("Dados atualizados!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
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

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    bu = cf1.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    fs = cf2.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    fu = cf3.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    if cf4.button("🔄", key="btn_refresh"): st.cache_data.clear(); st.rerun()

    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        
        if bu: df_g = df_g[df_g['ALUNO'].astype(str).str.contains(bu, case=False) | df_g['ID'].astype(str).str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]

        st.markdown('<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>', unsafe_allow_html=True)
        cols_html = "".join([f'<th>{h}</th>' for h in hd])
        st.markdown(f'{cols_html}</tr></thead><tbody>', unsafe_allow_html=True)

        # Usando colunas Streamlit dentro do wrapper para permitir interação
        for idx, r in df_g.iloc[::-1].iterrows():
            # Construindo a linha visualmente
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            
            col_list = st.columns([1, 0.8, 0.8, 0.5, 0.5, 1, 1, 2, 1.2, 1.2, 1.2, 1, 1.5, 2, 1, 1])
            
            col_list[0].markdown(f"<span class='status-badge {sc}'>{r['STATUS']}</span>", unsafe_allow_html=True)
            col_list[1].write(r['UNID.'])
            col_list[2].write(r['TURMA'])
            col_list[3].write(r['10C'])
            col_list[4].write(r['ING'])
            col_list[5].write(r['DT_CAD'])
            
            # Botão de ID que dispara o Modal
            if col_list[6].button(str(r['ID']), key=f"id_{r['ID']}_{idx}"):
                if "original_data" in st.session_state: del st.session_state.original_data
                editar_aluno_dialog(idx, r.to_dict(), hd)
            
            col_list[7].markdown(f"<b style='color:#00f2ff'>{r['ALUNO']}</b>", unsafe_allow_html=True)
            col_list[8].write(r['TEL_RESP'])
            col_list[9].write(r['TEL_ALU'])
            col_list[10].write(r['CPF'])
            col_list[11].write(r['CIDADE'])
            col_list[12].write(r['CURSO'])
            col_list[13].write(r['PAGTO'])
            col_list[14].write(r['VEND.'])
            col_list[15].write(r['DT_MAT'])
            
        st.markdown('</tbody></table></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS ---
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
    except Exception as e: st.error(f"Erro: {e}")
