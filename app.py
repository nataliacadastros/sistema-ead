import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZAÇÃO DE ESTADOS DE CONFIGURAÇÃO (APENAS MOBILE) ---
if "cor_label_mob" not in st.session_state: st.session_state.cor_label_mob = "#2ecc71"
if "alt_input_mob" not in st.session_state: st.session_state.alt_input_mob = 35  # Padrão mobile mais alto
if "fonte_tabela_mob" not in st.session_state: st.session_state.fonte_tabela_mob = 9
if "altura_tabela_ger" not in st.session_state: st.session_state.altura_tabela_ger = 600

# --- CSS COM MEDIA QUERY (DIFERENCIA PC DE MOBILE) ---
st.markdown(f"""
    <style>
    /* --- ESTILO PADRÃO (COMPUTADOR) --- */
    .stApp {{ background-color: #1a2436; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; max-width: 99% !important; }}
    
    .stTabs [data-baseweb="tab-list"] {{ background-color: #1a3a5a; }}
    .stTabs [data-baseweb="tab"] {{ height: 48px; color: white !important; font-weight: 600; padding: 0 30px; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 4px solid #2ecc71 !important; }}

    /* Inputs e Labels no PC (Fixos para não quebrar o que já está perfeito) */
    div[data-testid="stTextInput"] > div {{ min-height: 22px !important; height: 22px !important; }}
    .stTextInput input {{ background-color: white !important; color: black !important; height: 22px !important; font-size: 11px !important; }}
    label {{ color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; display: flex; align-items: center; justify-content: flex-end; padding-right: 15px; height: 22px !important; }}
    
    /* Tabela no PC */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {{ font-size: 10px !important; }}

    /* --- ESTILO EXCLUSIVO PARA MOBILE (ABAIXO DE 768px) --- */
    @media (max-width: 768px) {{
        /* Aplica a cor de label configurada */
        label {{ 
            color: {st.session_state.cor_label_mob} !important; 
            height: {st.session_state.alt_input_mob}px !important;
            justify-content: flex-start !important; /* No mobile label fica em cima */
        }}
        
        /* Aplica a altura de input configurada */
        div[data-testid="stTextInput"] > div, .stTextInput input {{ 
            min-height: {st.session_state.alt_input_mob}px !important; 
            height: {st.session_state.alt_input_mob}px !important; 
        }}

        /* Aplica o tamanho de fonte da tabela configurada */
        [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {{ 
            font-size: {st.session_state.fonte_tabela_mob}px !important; 
        }}
    }}

    /* MOCKUP CELULAR PREVIEW */
    .mobile-frame {{
        width: 320px; height: 550px; border: 10px solid #333; border-radius: 25px;
        margin: 0 auto; overflow-y: auto; background-color: #1a2436; padding: 15px;
    }}
    
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÕES ---
def campo_horizontal(label, key, value=""):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value)

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "🎨 CONFIG. MOBILE"])

# ================= ABA 1: CADASTRO =================
with abas[0]:
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    with col_form:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("CIDADE:", "cid_f")
        campo_horizontal("CURSO:", "curso_field")
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input", value=date.today().strftime("%d/%m/%Y"))
        
        st.write("")
        if st.button("💾 SALVAR ALUNO"):
            if st.session_state.nome_alu:
                aluno = {"ID": st.session_state.id_alu, "Aluno": st.session_state.nome_alu, "Cidade": st.session_state.cid_f, "Curso": st.session_state.curso_field, "Pagamento": st.session_state.pagto_input, "Vendedor": st.session_state.vend_f, "Data": st.session_state.data_input}
                if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
                st.session_state.lista_previa.append(aluno)
                st.rerun()

# ================= ABA 2: GERENCIAMENTO =================
with abas[1]:
    st.write("")
    t1, t2 = st.columns([3, 1])
    with t1: busca = st.text_input("Filtro", placeholder="🔍 Pesquisar...", label_visibility="collapsed").upper()
    with t2: 
        if st.button("🔄 Sync"): 
            st.cache_data.clear()
            st.rerun()
    
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        dados_ex = dados.iloc[::-1]
        if busca:
            mask = dados_ex.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_ex = dados_ex[mask]
        
        st.dataframe(dados_ex, use_container_width=True, hide_index=True, height=st.session_state.altura_tabela_ger)
    except:
        st.error("Conecte a planilha.")

# ================= ABA 3: CONFIGURAÇÃO MOBILE (ISOLADA) =================
with abas[2]:
    st.subheader("🛠️ Ajustes Exclusivos para Mobile")
    st.info("As alterações aqui só serão visíveis quando o site for aberto em um celular.")
    
    c_config, c_preview = st.columns([1, 1.2])
    
    with c_config:
        st.session_state.cor_label_mob = st.color_picker("Cor das Labels no Mobile", st.session_state.cor_label_mob)
        st.session_state.alt_input_mob = st.slider("Altura dos campos no Mobile (px)", 20, 60, st.session_state.alt_input_mob)
        st.session_state.fonte_tabela_mob = st.slider("Fonte da tabela no Mobile (px)", 7, 12, st.session_state.fonte_tabela_mob)
        st.session_state.altura_tabela_ger = st.number_input("Altura do frame da lista (px)", 200, 1000, st.session_state.altura_tabela_ger)
        
        if st.button("APLICAR NO MOBILE"):
            st.rerun()

    with c_preview:
        st.markdown(f"""
            <div class="mobile-frame">
                <p style="text-align:center; font-size:10px; color:#666;">PRÉVIA DO CELULAR</p>
                <label style="color:{st.session_state.cor_label_mob}; font-weight:bold; font-size:12px; justify-content:flex-start;">NOME ALUNO:</label>
                <div style="background:white; height:{st.session_state.alt_input_mob}px; border-radius:4px; margin-bottom:15px;"></div>
                
                <div style="background:white; height:150px; border-radius:4px; overflow:hidden; margin-top:20px;">
                    <table style="width:100%; font-size:{st.session_state.fonte_tabela_mob}px; color:black; border-collapse:collapse;">
                        <tr style="background:#ddd;"><th>ID</th><th>Aluno</th></tr>
                        <tr><td>01</td><td>EXEMPLO MOBILE</td></tr>
                    </table>
                </div>
            </div>
        """, unsafe_allow_html=True)
