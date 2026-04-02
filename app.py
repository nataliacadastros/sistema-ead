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
    
    /* ESTILO DOS INPUTS */
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; }
    .stTextInput input, .stTextArea textarea { 
        background-color: white !important; color: black !important; 
        text-transform: uppercase !important; border-radius: 5px !important; 
    }
    
    /* TABELA DE GERENCIAMENTO CUSTOMIZADA */
    .table-header { background: #1f295a; color: #00f2ff; padding: 10px; font-weight: bold; font-size: 11px; border-radius: 5px; text-align: left; }
    .table-row { border-bottom: 1px solid #1f295a; padding: 5px 0; align-items: center; }
    
    .status-badge { padding: 2px 8px; border-radius: 10px; font-size: 9px; font-weight: bold; }
    .status-ativo { background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* BOTÃO LÁPIS MINIMALISTA */
    div[data-testid="stColumn"] button {
        background: transparent !important; border: none !important; color: #00f2ff !important;
        padding: 0 !important; font-size: 16px !important; line-height: 1 !important;
    }
    div[data-testid="stColumn"] button:hover { color: #ff007a !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS DE SESSÃO ---
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

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
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        s_ge = f"g_{st.session_state.reset_geral}"
        campos = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("CURSO:", f"input_curso_{s_al}"), ("PAGTO:", f"f_pagto_{s_al}"), ("VENDEDOR:", f"f_vend_{s_ge}"), ("CIDADE:", f"f_cid_{s_ge}"), ("DATA MATRÍCULA:", f"f_data_{s_ge}")]
        
        for l, k in campos:
            cl, ci = st.columns([1.5, 3.5])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        if st.button("💾 SALVAR ALUNO"):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({
                    "ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                    "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_{s_al}"].upper(),
                    "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                })
                st.session_state.reset_aluno += 1; st.rerun()
        
        if st.session_state.lista_previa:
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True)
            if st.button("📤 ENVIAR PARA PLANILHA"):
                try:
                    creds = st.secrets["connections"]["gsheets"]
                    client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
                    d_f = []
                    for a in st.session_state.lista_previa:
                        d_f.append(["ATIVO", "MGA", "A DEFINIR", "NÃO", "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], "", "", "", a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                    ws.insert_rows(d_f, row=2)
                    st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.cache_data.clear(); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_g = conn.read(ttl="0s").fillna("")
    hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
    df_g.columns = hd[:len(df_g.columns)]

    # Filtro Simples
    busca = st.text_input("🔍 Buscar Aluno...", placeholder="Digite nome ou ID").upper()
    if busca:
        df_g = df_g[df_g['ALUNO'].astype(str).str.contains(busca) | df_g['ID'].astype(str).str.contains(busca)]

    # Cabeçalho da Tabela
    c_h = st.columns([0.3, 0.8, 0.8, 3, 2, 2])
    cols_h = ["", "STATUS", "ID", "ALUNO", "CURSO", "PAGAMENTO"]
    for col, texto in zip(c_h, cols_h): col.markdown(f"<div class='table-header'>{texto}</div>", unsafe_allow_html=True)

    # Linhas da Tabela
    for i, row in df_g.iloc[::-1].head(30).iterrows():
        c = st.columns([0.3, 0.8, 0.8, 3, 2, 2])
        
        # Botão Editar (Lápis) - Seta o estado e dá rerun sem mudar aba
        if c[0].button("✏️", key=f"edit_btn_{row['ID']}"):
            st.session_state.edit_id = row['ID']
            st.rerun()
            
        st_class = "status-ativo" if row['STATUS'] == "ATIVO" else "status-cancelado"
        c[1].markdown(f"<span class='status-badge {st_class}'>{row['STATUS']}</span>", unsafe_allow_html=True)
        c[2].write(row['ID'])
        c[3].write(f"**{row['ALUNO']}**")
        c[4].write(row['CURSO'])
        c[5].write(row['PAGTO'])

    # --- FRAME DE EDIÇÃO (Aparece abaixo da tabela ao clicar no lápis) ---
    if st.session_state.edit_id:
        st.markdown("---")
        st.subheader(f"🛠️ Editando Cadastro: {st.session_state.edit_id}")
        
        # Busca dados atuais para preencher o formulário
        aluno_atual = df_g[df_g['ID'] == st.session_state.edit_id].iloc[0]
        
        with st.form("form_edit"):
            row1 = st.columns(4)
            e_status = row1[0].selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if aluno_atual['STATUS']=="ATIVO" else 1)
            e_unid = row1[1].text_input("UNIDADE", value=aluno_atual['UNID.'])
            e_turma = row1[2].text_input("TURMA", value=aluno_atual['TURMA'])
            e_data_cad = row1[3].text_input("DATA CADASTRO", value=aluno_atual['DT_CAD'])
            
            row2 = st.columns([3, 1, 1])
            e_nome = row2[0].text_input("NOME COMPLETO", value=aluno_atual['ALUNO'])
            e_id = row2[1].text_input("ID", value=aluno_atual['ID'])
            e_cpf = row2[2].text_input("CPF", value=aluno_atual['CPF'])
            
            e_curso = st.text_input("CURSO", value=aluno_atual['CURSO'])
            e_pagto = st.text_area("PAGAMENTO / OBSERVAÇÕES", value=aluno_atual['PAGTO'])
            
            b_save, b_cancel = st.columns(2)
            if b_save.form_submit_button("✅ SALVAR ALTERAÇÕES"):
                try:
                    creds = st.secrets["connections"]["gsheets"]
                    client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0)
                    
                    # Localiza a linha pelo ID (Coluna G = índice 7)
                    cell = ws.find(str(st.session_state.edit_id), in_col=7)
                    if cell:
                        # Atualiza as colunas principais
                        ws.update_cell(cell.row, 1, e_status)
                        ws.update_cell(cell.row, 2, e_unid)
                        ws.update_cell(cell.row, 3, e_turma)
                        ws.update_cell(cell.row, 6, e_data_cad)
                        ws.update_cell(cell.row, 7, e_id.upper())
                        ws.update_cell(cell.row, 8, e_nome.upper())
                        ws.update_cell(cell.row, 11, e_cpf)
                        ws.update_cell(cell.row, 13, e_curso.upper())
                        ws.update_cell(cell.row, 14, e_pagto.upper())
                        
                        st.success("Cadastro atualizado com sucesso!")
                        st.session_state.edit_id = None
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            
            if b_cancel.form_submit_button("❌ CANCELAR"):
                st.session_state.edit_id = None
                st.rerun()

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            df_r.columns = [c.strip() for c in df_r.columns]
            # Exemplo de Dashboard simples
            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Matrículas", len(df_r))
            c2.metric("Ativos", len(df_r[df_r['STATUS'] == "ATIVO"]))
            c3.metric("Cancelados", len(df_r[df_r['STATUS'] == "CANCELADO"]))
    except: st.write("Carregando dados dos relatórios...")
