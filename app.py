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
    .main .block-container { padding-top: 45px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; }
    
    /* Campos de texto */
    .stTextInput input { 
        background-color: white !important; color: black !important; 
        text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; 
    }

    /* Tabela Customizada */
    .custom-table-wrapper {
        width: 100%; max-height: 600px; overflow: auto;
        background-color: #121629; border: 2px solid #1f295a; border-radius: 10px;
    }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; padding: 15px; font-size: 11px; position: sticky; top: 0; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; }

    /* Badges */
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* Botão de ID que parece link */
    .stButton button[kind="secondary"] {
        background-color: transparent !important; color: #00f2ff !important;
        border: 1px solid #00f2ff !important; padding: 0px 5px !important; height: 22px !important;
    }
    
    /* Relatórios Card */
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÃO DE EDIÇÃO (JANELA MODAL) ---
@st.dialog("Editar Dados do Aluno", width="large")
def modal_editar_aluno(id_aluno, dados_atuais, row_index):
    st.write(f"Editando ID: **{id_aluno}**")
    
    # Backup para desfazer
    if f"backup_{id_aluno}" not in st.session_state:
        st.session_state[f"backup_{id_aluno}"] = dados_atuais.copy()

    col_undo, _ = st.columns([0.1, 0.9])
    if col_undo.button("↩️", help="Desfazer alterações"):
        for k, v in st.session_state[f"backup_{id_aluno}"].items():
            st.session_state[f"modal_{k}"] = str(v)
        st.rerun()

    novos_dados_dict = {}
    c1, c2 = st.columns(2)
    
    campos = list(dados_atuais.keys())
    for i, campo in enumerate(campos):
        col = c1 if i % 2 == 0 else c2
        key_modal = f"modal_{campo}"
        if key_modal not in st.session_state:
            st.session_state[key_modal] = str(dados_atuais[campo])
        
        novos_dados_dict[campo] = col.text_input(campo, key=key_modal)

    st.write("---")
    b_salvar, b_sair = st.columns(2)
    
    if b_salvar.button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
        try:
            creds = st.secrets["connections"]["gsheets"]
            client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
            ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
            
            # Ordem correta das colunas para a planilha
            ordem_colunas = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
            lista_para_update = [novos_dados_dict.get(col, "") for col in ordem_colunas]
            
            ws.update(f'A{row_index + 2}:P{row_index + 2}', [lista_para_update])
            st.success("Atualizado com sucesso!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    if b_sair.button("CANCELAR", use_container_width=True):
        st.rerun()

# --- FUNÇÕES AUXILIARES ---
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
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
    if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
    if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
    
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
    bu = cf1.text_input("🔍 Buscar...", placeholder="Nome ou ID", label_visibility="collapsed")
    fs = cf2.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], label_visibility="collapsed")
    fu = cf3.selectbox("Unidade", ["Todos", "MGA"], label_visibility="collapsed")
    if cf4.button("🔄"): st.cache_data.clear(); st.rerun()

    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        
        if bu: df_g = df_g[df_g['ALUNO'].astype(str).str.contains(bu, case=False) | df_g['ID'].astype(str).str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]

        # Tabela em colunas Streamlit para permitir botões clicáveis no ID
        st.markdown('<div class="custom-table-wrapper">', unsafe_allow_html=True)
        
        # Cabeçalho manual
        cols_size = [1.2, 0.8, 1, 0.5, 0.5, 1, 1, 2, 1.2, 1.2, 1.2, 1.2, 1.5, 2, 1.2, 1]
        h_cols = st.columns(cols_size)
        for i, h in enumerate(hd): h_cols[i].markdown(f"**{h}**")
        st.markdown("---")

        for idx, r in df_g.iloc[::-1].iterrows():
            r_cols = st.columns(cols_size)
            
            # Status Badge
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            r_cols[0].markdown(f"<span class='status-badge {sc}'>{r['STATUS']}</span>", unsafe_allow_html=True)
            
            r_cols[1].write(r['UNID.'])
            r_cols[2].write(r['TURMA'])
            r_cols[3].write(r['10C'])
            r_cols[4].write(r['ING'])
            r_cols[5].write(r['DT_CAD'])
            
            # O ID agora é um BOTÃO que abre a JANELA MODAL
            if r_cols[6].button(str(r['ID']), key=f"btn_{r['ID']}_{idx}", kind="secondary"):
                modal_editar_aluno(r['ID'], r.to_dict(), idx)
            
            r_cols[7].markdown(f"<span style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</span>", unsafe_allow_html=True)
            r_cols[8].write(r['TEL_RESP'])
            r_cols[9].write(r['TEL_ALU'])
            r_cols[10].write(r['CPF'])
            r_cols[11].write(r['CIDADE'])
            r_cols[12].write(r['CURSO'])
            r_cols[13].write(r['PAGTO'])
            r_cols[14].write(r['VEND.'])
            r_cols[15].write(r['DT_MAT'])
            
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

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
                df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido)
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro nos relatórios: {e}")
