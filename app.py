import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZAÇÃO DE ESTADOS DE CONFIGURAÇÃO VISUAL ---
if "cor_label_mob" not in st.session_state: st.session_state.cor_label_mob = "#2ecc71"
if "alt_input_cad" not in st.session_state: st.session_state.alt_input_cad = 22
if "altura_tabela_ger" not in st.session_state: st.session_state.altura_tabela_ger = 600
if "fonte_tabela_ger" not in st.session_state: st.session_state.fonte_tabela_ger = 10

# --- CSS DINÂMICO (LIGADO AO PREVIEW) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #1a2436; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; max-width: 99% !important; }}

    /* MENU SUPERIOR */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px; background-color: #1a3a5a; padding: 0px;
        border-bottom: 2px solid #2c5282;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 48px; color: #ffffff !important; font-weight: 600;
        border: none; background-color: transparent; padding: 0px 30px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important;
    }}

    /* INPUTS BRANCOS CONFIGURÁVEIS */
    div[data-testid="stTextInput"] > div {{ 
        min-height: {st.session_state.alt_input_cad}px !important; 
        height: {st.session_state.alt_input_cad}px !important; 
    }}
    .stTextInput input {{ 
        background-color: white !important; color: black !important; 
        height: {st.session_state.alt_input_cad}px !important; 
        text-transform: uppercase !important; border-radius: 2px !important; 
        font-size: 11px !important; padding: 0px 8px !important;
    }}
    
    /* LABELS CONFIGURÁVEIS */
    label {{ 
        color: {st.session_state.cor_label_mob} !important; 
        font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; justify-content: flex-end; padding-right: 15px;
        height: {st.session_state.alt_input_cad}px !important;
    }}
    
    /* BOTÕES */
    div.stButton > button {{
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 38px !important; border: none !important; width: 100% !important;
    }}

    /* TABELAS */
    .stDataFrame {{ background-color: white !important; color: black !important; border-radius: 4px; }}
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {{ 
        font-size: {st.session_state.fonte_tabela_ger}px !important; 
    }}

    /* MOCKUP CELULAR PREVIEW */
    .mobile-frame {{
        width: 320px; height: 550px; border: 10px solid #333; border-radius: 25px;
        margin: 0 auto; overflow-y: auto; background-color: #1a2436; padding: 15px;
    }}
    
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS DE DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []

# --- FUNÇÕES DE LÓGICA ---
def campo_horizontal(label, key, value=""):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value)

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CURSO BÔNUS"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO"
    st.session_state.pagto_input = base

# --- ABAS ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "🎨 CONFIGURAÇÃO VISUAL"])

# ================= ABA 1: CADASTRO (FUNCIONANDO) =================
with abas[0]:
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    with col_form:
        st.write("")
        id_alu = campo_horizontal("ID:", "id_alu")
        nome_alu = campo_horizontal("ALUNO:", "nome_alu")
        cid_f = campo_horizontal("CIDADE:", "cid_f")
        curso_f = campo_horizontal("CURSO:", "curso_field")
        pagto_f = campo_horizontal("PAGAMENTO:", "pagto_input")
        vend_f = campo_horizontal("VENDEDOR:", "vend_f")
        data_f = campo_horizontal("DATA:", "data_input", value=date.today().strftime("%d/%m/%Y"))

        st.write("")
        c_sel = st.columns(3)
        with c_sel[0]: st.checkbox("IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with c_sel[1]: st.checkbox("BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with c_sel[2]: st.checkbox("CONFIRMA", key="check_conf", on_change=atualizar_pagto)

        st.write("")
        c_btns = st.columns(2)
        with c_btns[0]:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(), "Curso": st.session_state.curso_field.upper(),
                        "Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with c_btns[1]:
            if st.button("📤 ENVIAR PARA PLANILHA"):
                if st.session_state.lista_previa:
                    df_existente = conn.read(ttl="0s").fillna("")
                    df_novo = pd.DataFrame(st.session_state.lista_previa)
                    df_final = pd.concat([df_existente, df_novo], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.success("Dados enviados!")
                    st.rerun()

    st.write("---")
    st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# ================= ABA 2: GERENCIAMENTO (FUNCIONANDO) =================
with abas[1]:
    st.write("")
    t1, t2 = st.columns([3, 1])
    with t1: busca = st.text_input("Busca", placeholder="🔍 Pesquisar...", label_visibility="collapsed").upper()
    with t2: 
        if st.button("🔄 Atualizar Base"): 
            st.cache_data.clear()
            st.rerun()
    
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        
        dados_exibicao = dados.iloc[::-1] # Novos no topo
        if busca:
            mask = dados_exibicao.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_exibicao = dados_exibicao[mask]
        
        st.dataframe(
            dados_exibicao, 
            use_container_width=True, 
            hide_index=True, 
            height=st.session_state.altura_tabela_ger, # Altura configurável
            column_config={
                "ID": st.column_config.TextColumn("ID", width=50),
                "Aluno": st.column_config.TextColumn("Aluno", width=200),
                "Pagamento": st.column_config.TextColumn("Pagamento", width=350),
            }
        )
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

# ================= ABA 3: CONFIGURAÇÃO VISUAL (DINÂMICA) =================
with abas[2]:
    st.markdown("### 🛠️ Painel de Controle de Design")
    
    c_config, c_preview = st.columns([1, 1.2])
    
    with c_config:
        st.session_state.cor_label_mob = st.color_picker("Cor das Labels (Nomes dos campos)", st.session_state.cor_label_mob)
        st.session_state.alt_input_cad = st.slider("Altura dos campos de preenchimento (px)", 15, 50, st.session_state.alt_input_cad)
        st.session_state.altura_tabela_ger = st.number_input("Altura total da tabela de gerenciamento (px)", 200, 1200, st.session_state.altura_tabela_ger)
        st.session_state.fonte_tabela_ger = st.slider("Tamanho da fonte dos dados (px)", 7, 16, st.session_state.fonte_tabela_ger)
        
        if st.button("APLICAR ALTERAÇÕES VISUAIS"):
            st.rerun()

    with c_preview:
        st.markdown(f"""
            <div class="mobile-frame">
                <p style="text-align:center; font-size:10px; color:#555;">MOCKUP MOBILE</p>
                <label style="color:{st.session_state.cor_label_mob}; font-weight:bold; font-size:11px;">ALUNO:</label>
                <div style="background:white; height:{st.session_state.alt_input_cad}px; border-radius:2px; margin-bottom:10px;"></div>
                <button style="width:100%; background:#2ecc71; color:white; border:none; padding:8px; border-radius:4px; font-weight:bold; font-size:11px;">
                    BOTÃO SALVAR
                </button>
                <div style="margin-top:20px; background:white; height:150px; border-radius:4px; overflow:hidden;">
                    <table style="width:100%; font-size:{st.session_state.fonte_tabela_ger}px; color:black; border-collapse:collapse;">
                        <tr style="background:#eee;"><th>ID</th><th>Aluno</th></tr>
                        <tr><td>1</td><td>Teste Exemplo</td></tr>
                    </table>
                </div>
            </div>
        """, unsafe_allow_html=True)
