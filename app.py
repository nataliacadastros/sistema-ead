import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CSS DEFINITIVO (RESPONSIVO + SIMULADOR) ---
st.markdown("""
    <style>
    /* Estilo Base */
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 99% !important; }

    /* MENU SUPERIOR */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px; background-color: #1a3a5a; padding: 0px;
        border-bottom: 2px solid #2c5282;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px; color: #ffffff !important; font-weight: 600;
        border: none; background-color: transparent; padding: 0px 30px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important;
    }

    /* INPUTS BRANCOS */
    div[data-testid="stTextInput"] > div { min-height: 22px !important; }
    .stTextInput input { 
        background-color: white !important; color: black !important; 
        height: 22px !important; text-transform: uppercase !important; 
        border-radius: 2px !important; font-size: 11px !important; padding: 0px 8px !important;
    }
    
    /* LABELS VERDES */
    label { 
        color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; 
        display: flex; align-items: center; justify-content: flex-end; padding-right: 15px;
    }
    
    /* BOTÕES */
    div.stButton > button {
        background-color: #2ecc71 !important; color: white !important;
        font-weight: bold !important; height: 38px !important; border-radius: 4px !important;
        width: 100% !important; border: none !important;
    }

    /* TABELAS */
    .stDataFrame { background-color: white !important; color: black !important; border-radius: 4px; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { font-size: 10px !important; }

    /* CSS DO SIMULADOR MOBILE (MOCKUP) */
    .mobile-frame {
        width: 320px;
        height: 580px;
        border: 12px solid #333;
        border-radius: 30px;
        margin: 0 auto;
        overflow-y: auto;
        background-color: #1a2436;
        padding: 15px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
    }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []

# --- FUNÇÃO CAMPO FORMULÁRIO ---
def campo_horizontal(label, key, value=""):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value)

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "🎨 PREVIEW MOBILE"])

# ================= ABA 1: CADASTRO =================
with abas[0]:
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    with col_form:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field")
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input")

        st.write("")
        c_sel = st.columns(3)
        with c_sel[0]: st.checkbox("IN-GLÊS", key="check_lib")
        with c_sel[1]: st.checkbox("BÔNUS", key="check_bonus")
        with c_sel[2]: st.checkbox("CONFIRMA", key="check_conf")

        st.write("")
        c_btns = st.columns(2)
        with c_btns[0]:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {"ID": st.session_state.id_alu, "Aluno": st.session_state.nome_alu, "Cidade": st.session_state.cid_f, "Curso": st.session_state.curso_field, "Pagamento": st.session_state.pagto_input, "Vendedor": st.session_state.vend_f, "Data": st.session_state.data_input}
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with c_btns[1]:
            if st.button("📤 FINALIZAR"):
                # Enviar para Sheets...
                st.session_state.lista_previa = []
                st.rerun()

    st.write("")
    st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# ================= ABA 2: GERENCIAMENTO =================
with abas[1]:
    st.write("")
    t1, t2 = st.columns([3, 1])
    with t1: busca = st.text_input("Busca", placeholder="🔍 Pesquisar...", label_visibility="collapsed").upper()
    with t2: 
        if st.button("🔄 Sync"): st.rerun()
    
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Ordem Invertida (Novos no Topo)
        dados_exibicao = dados.iloc[::-1]

        if busca:
            mask = dados_exibicao.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_exibicao = dados_exibicao[mask]
        
        st.dataframe(
            dados_exibicao, 
            use_container_width=True, 
            hide_index=True, 
            height=500,
            column_config={
                "ID": st.column_config.TextColumn("ID", width=50),
                "Data": st.column_config.TextColumn("Dt", width=70),
                "Vendedor": st.column_config.TextColumn("Vend", width=90),
                "Cidade": st.column_config.TextColumn("Cid", width=100),
                "Aluno": st.column_config.TextColumn("Aluno", width=200),
                "Curso": st.column_config.TextColumn("Cur", width=150),
                "Pagamento": st.column_config.TextColumn("Pag", width=300),
            }
        )
    except:
        st.error("Erro ao carregar dados.")

# ================= ABA 3: PREVIEW MOBILE (SIMULADOR) =================
with abas[2]:
    st.write("")
    col_ctrl, col_sim = st.columns([1, 1.5])
    
    with col_ctrl:
        st.subheader("⚙️ Ajustes de Visualização")
        st.info("Use este painel para testar cores e tamanhos antes de aplicar no código principal.")
        cor_tema = st.color_picker("Cor Principal (Verde)", "#2ecc71")
        fonte_tabela = st.slider("Tamanho Fonte Tabela (px)", 8, 14, 10)
        largura_col = st.number_input("Largura Coluna Aluno", 100, 400, 200)

    with col_sim:
        st.markdown(f"""
            <div class="mobile-frame">
                <div style="text-align:center; padding-bottom:10px; border-bottom:1px solid #333;">
                    <span style="color:{cor_tema}; font-weight:bold; font-size:14px;">Simulação Mobile</span>
                </div>
                <div style="margin-top:20px;">
                    <label style="color:{cor_tema}; font-size:10px; display:block; margin-bottom:2px;">ALUNO:</label>
                    <div style="background:white; height:22px; border-radius:2px; margin-bottom:10px;"></div>
                    
                    <label style="color:{cor_tema}; font-size:10px; display:block; margin-bottom:2px;">CURSO:</label>
                    <div style="background:white; height:22px; border-radius:2px; margin-bottom:10px;"></div>
                    
                    <button style="width:100%; background:{cor_tema}; color:white; border:none; padding:8px; border-radius:4px; font-weight:bold; font-size:12px; margin-top:10px;">
                        SALVAR ALUNO
                    </button>
                    
                    <div style="margin-top:25px; background:white; border-radius:4px; padding:5px; height:150px;">
                        <table style="width:100%; color:black; font-size:{fonte_tabela}px; border-collapse:collapse;">
                            <tr style="border-bottom:1px solid #ddd; text-align:left;">
                                <th>ID</th><th>Aluno</th><th>Vend</th>
                            </tr>
                            <tr><td>10</td><td>JOÃO SILVA</td><td>MARIA</td></tr>
                            <tr style="background:#f9f9f9;"><td>11</td><td>ANA COSTA</td><td>JOSÉ</td></tr>
                        </table>
                    </div>
                </div>
                <p style="text-align:center; font-size:8px; color:#555; margin-top:20px;">Fim da tela simulada</p>
            </div>
        """, unsafe_allow_html=True)
