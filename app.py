import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZAÇÃO DE ESTADOS PARA O PREVIEW ---
if "cor_fundo_mob" not in st.session_state: st.session_state.cor_fundo_mob = "#1a2436"
if "cor_label_mob" not in st.session_state: st.session_state.cor_label_mob = "#2ecc71"
if "cor_btn_mob" not in st.session_state: st.session_state.cor_btn_mob = "#2ecc71"
if "alt_input_mob" not in st.session_state: st.session_state.alt_input_mob = 22
if "larg_input_mob" not in st.session_state: st.session_state.larg_input_mob = 100
if "fonte_tab_mob" not in st.session_state: st.session_state.fonte_tab_mob = 10

# --- CSS BASE (PC) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #1a2436; color: white; }}
    .block-container {{ padding-top: 0.5rem !important; max-width: 99% !important; }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: #1a3a5a; }}
    .stTabs [data-baseweb="tab"] {{ color: white !important; font-weight: 600; padding: 0 30px; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 4px solid #2ecc71 !important; }}
    
    /* Moldura do Celular no Preview */
    .mobile-frame {{
        width: 340px;
        height: 600px;
        border: 12px solid #333;
        border-radius: 35px;
        margin: 0 auto;
        overflow-y: auto;
        background-color: {st.session_state.cor_fundo_mob};
        padding: 20px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.6);
        position: relative;
    }}
    .mobile-frame::-webkit-scrollbar {{ width: 3px; }}
    .mobile-frame::-webkit-scrollbar-thumb {{ background: #444; }}
    
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "🎨 PREVIEW MOBILE"])

# ================= ABA 1 & 2 (MANTIDAS CONFORME VERSÕES ANTERIORES) =================
with abas[0]:
    st.info("Tela de Cadastro ativa no modo padrão.")
    # (O código de cadastro entra aqui como nas versões anteriores)

with abas[1]:
    st.info("Tela de Gerenciamento ativa no modo padrão.")
    # (O código de gerenciamento entra aqui como nas versões anteriores)

# ================= ABA 3: PREVIEW MOBILE TOTALMENTE CONFIGURÁVEL =================
with abas[2]:
    st.markdown("### 🛠️ Oficina de Design Mobile")
    st.write("Ajuste as configurações abaixo e veja o resultado no simulador à direita.")
    
    col_ctrl, col_sim = st.columns([1, 1.2])
    
    with col_ctrl:
        with st.expander("🎨 Cores e Estilo", expanded=True):
            st.session_state.cor_fundo_mob = st.color_picker("Cor de Fundo do Celular", st.session_state.cor_fundo_mob)
            st.session_state.cor_label_mob = st.color_picker("Cor das Labels (Nomes)", st.session_state.cor_label_mob)
            st.session_state.cor_btn_mob = st.color_picker("Cor do Botão Salvar", st.session_state.cor_btn_mob)
        
        with st.expander("📐 Dimensões dos Campos", expanded=True):
            st.session_state.alt_input_mob = st.slider("Altura dos Campos (px)", 15, 45, st.session_state.alt_input_mob)
            st.session_state.larg_input_mob = st.slider("Largura dos Campos (%)", 50, 100, st.session_state.larg_input_mob)
            st.session_state.fonte_tab_mob = st.slider("Tamanho da Letra na Tabela (px)", 7, 14, st.session_state.fonte_tab_mob)
        
        st.warning("⚠️ Nota: Estas alterações são visuais para este preview. Para aplicá-las no site real, você deve atualizar os valores no bloco de CSS do código.")

    with col_sim:
        # CONSTRUÇÃO DO HTML DO CELULAR USANDO AS VARIÁVEIS
        html_celular = f"""
        <div class="mobile-frame">
            <!-- Notch do celular -->
            <div style="width: 100px; height: 18px; background: #333; margin: -20px auto 10px auto; border-radius: 0 0 10px 10px;"></div>
            
            <p style="text-align:center; color:#888; font-size:10px; margin-bottom:20px;">Operadora v.2026</p>
            
            <label style="color:{st.session_state.cor_label_mob}; font-weight:bold; font-size:11px;">NOME DO ALUNO:</label>
            <div style="background:white; height:{st.session_state.alt_input_mob}px; width:{st.session_state.larg_input_mob}%; border-radius:4px; margin-bottom:12px; border:1px solid #ddd;"></div>
            
            <label style="color:{st.session_state.cor_label_mob}; font-weight:bold; font-size:11px;">CURSO:</label>
            <div style="background:white; height:{st.session_state.alt_input_mob}px; width:{st.session_state.larg_input_mob}%; border-radius:4px; margin-bottom:12px; border:1px solid #ddd;"></div>
            
            <button style="width:100%; background:{st.session_state.cor_btn_mob}; color:white; border:none; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; margin-top:15px; cursor: pointer;">
                💾 SALVAR MATRÍCULA
            </button>
            
            <div style="margin-top:30px; background:white; border-radius:4px; padding:8px; min-height:180px;">
                <p style="color:black; font-weight:bold; font-size:10px; border-bottom:1px solid #eee; padding-bottom:5px;">LISTA RECENTE</p>
                <table style="width:100%; color:black; font-size:{st.session_state.fonte_tab_mob}px; border-collapse:collapse; margin-top:5px;">
                    <tr style="text-align:left; background:#f2f2f2;">
                        <th style="padding:4px;">ID</th><th style="padding:4px;">Aluno</th><th style="padding:4px;">Curso</th>
                    </tr>
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:4px;">102</td><td style="padding:4px;">MARCOS SILVA</td><td style="padding:4px;">ADM</td>
                    </tr>
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:4px;">103</td><td style="padding:4px;">JULIA COSTA</td><td style="padding:4px;">INFO</td>
                    </tr>
                </table>
            </div>
            
            <div style="width: 40px; height: 4px; background: #555; margin: 30px auto 0 auto; border-radius: 10px;"></div>
        </div>
        """
        st.markdown(html_celular, unsafe_allow_html=True)
