import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CSS AVANÇADO (DASHBOARD) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .block-container { padding-top: 0rem !important; max-width: 100% !important; }

    /* MENU SUPERIOR */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: #161b22; padding: 10px 30px;
        border-bottom: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px; color: #8b949e !important; font-weight: 600;
        border: none; background: none;
    }
    .stTabs [aria-selected="true"] {
        color: #2ecc71 !important; border-bottom: 2px solid #2ecc71 !important;
    }

    /* CARDS DE INDICADORES (KPIs) */
    .kpi-card {
        background-color: #161b22; border: 1px solid #30363d;
        padding: 20px; border-radius: 10px; text-align: center;
    }
    .kpi-value { font-size: 24px; font-weight: bold; color: #2ecc71; }
    .kpi-label { font-size: 14px; color: #8b949e; }

    /* CAMPOS DE INPUT E TABELA */
    div[data-testid="stTextInput"] > div { min-height: 30px !important; }
    .stTextInput>div>div>input { 
        background-color: #0d1117 !important; color: white !important; 
        border: 1px solid #30363d !important; border-radius: 5px !important;
    }
    
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 13px !important; }
    
    /* BOTÕES */
    div.stButton > button {
        background-color: #238636 !important; color: white !important;
        font-weight: bold !important; border: none !important; transition: 0.2s;
    }
    div.stButton > button:hover { background-color: #2ea043 !important; transform: translateY(-2px); }

    /* TABELA ESTILO ADMIN */
    .stDataFrame { background-color: #ffffff !important; border-radius: 8px !important; padding: 5px; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTADOS DO SISTEMA ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO CAMPO CADASTRO ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 2.5]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- NAVEGAÇÃO PRINCIPAL ---
abas = st.tabs(["📝 CADASTRO DE MATRÍCULAS", "🖥️ PAINEL DE GERENCIAMENTO", "📊 RELATÓRIOS ADM"])

# ================= ABA 1: CADASTRO =================
with abas[0]:
    _, col_form, _ = st.columns([1, 1.8, 1])
    with col_form:
        st.write("<br>", unsafe_allow_html=True)
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado)
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
            if st.button("💾 SALVAR NA LISTA"):
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
            if st.button("📄 FINALIZAR E ENVIAR"):
                # Lógica de envio omitida para brevidade
                st.session_state.lista_previa = []
                st.rerun()

    st.write("<br>", unsafe_allow_html=True)
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True)

# ================= ABA 2: GERENCIAMENTO =================
with abas[1]:
    st.write("<br>", unsafe_allow_html=True)
    
    # 1. LINHA DE INDICADORES (KPIs)
    try:
        df_total = conn.read(ttl="0s").fillna("")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">TOTAL DE MATRÍCULAS</div><div class="kpi-value">{len(df_total)}</div></div>', unsafe_allow_html=True)
        with kpi2:
            hoje = date.today().strftime("%d/%m/%Y")
            total_hoje = len(df_total[df_total.iloc[:, -1] == hoje]) if not df_total.empty else 0
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">MATRÍCULAS HOJE</div><div class="kpi-value">{total_hoje}</div></div>', unsafe_allow_html=True)
        with kpi3:
            vendedores = df_total['Vendedor'].nunique() if 'Vendedor' in df_total.columns else 0
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">EQUIPE ATIVA</div><div class="kpi-value">{vendedores}</div></div>', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">STATUS SISTEMA</div><div class="kpi-value" style="color:#3498db">ONLINE</div></div>', unsafe_allow_html=True)

        st.write("<br>", unsafe_allow_html=True)

        # 2. BARRA DE FERRAMENTAS (BUSCA E FILTROS)
        t1, t2 = st.columns([3, 1])
        with t1:
            pesquisa = st.text_input("🔍 Buscar aluno ou vendedor...", placeholder="Digite o nome para filtrar a tabela abaixo")
        with t2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("🔄 ATUALIZAR BASE"):
                st.rerun()

        # 3. TABELA DE DADOS ESTILIZADA
        if pesquisa:
            # Filtra em todas as colunas
            mask = df_total.astype(str).apply(lambda x: x.str.contains(pesquisa, case=False)).any(axis=1)
            df_total = df_total[mask]

        st.dataframe(
            df_total, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Status": st.column_config.BadgeColumn("Status"),
                "Data": st.column_config.DateColumn("Data da Matrícula")
            }
        )

    except Exception as e:
        st.error("Conecte a planilha para visualizar o painel de gerenciamento.")

# ================= ABA 3: RELATÓRIOS =================
with abas[2]:
    st.markdown("### 📈 Desempenho de Vendas")
    st.info("Gráficos de barras e pizzas por vendedor aparecerão aqui automaticamente conforme a base crescer.")
