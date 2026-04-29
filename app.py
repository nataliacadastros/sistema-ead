import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from openpyxl import Workbook, load_workbook
from io import BytesIO
from supabase import create_client

# --- 1. CONFIGURAÇÕES TÉCNICAS (DESIGN ORIGINAL) ---
st.set_page_config(page_title="SISTEMA UNIFICADO - Profissionaliza EAD", layout="wide", page_icon="🎓")

ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

# --- CONEXÃO EXCLUSIVA SUPABASE ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro nas credenciais do Supabase: {e}")
    st.stop()

# --- 2. FUNÇÕES DE SUPORTE (ORIGINAIS DO SEU CÓDIGO) ---

def carregar_usuarios():
    try:
        response = supabase.table("usuarios").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except:
        pass
    return pd.DataFrame(columns=["usuario", "senha", "nivel"])

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf))

def formatar_nome_proprio(nome):
    preposicoes = {'Da', 'De', 'Di', 'Do', 'Du', 'Dos', 'Das', 'E'}
    palavras = nome.strip().title().split()
    return " ".join([p if p not in preposicoes else p.lower() for p in palavras])

def formatar_whatsapp(tel):
    d = re.sub(r'\D', '', str(tel))
    if len(d) == 11:
        return f"({d[:2]}) {d[2]} {d[3:7]}-{d[7:]}"
    return d

# --- 3. LÓGICA DE LOGIN (EXATA AO ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_ativo = ""
    st.session_state.nivel_ativo = ""
if 'dados_aluno' not in st.session_state:
    st.session_state.dados_aluno = None

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Profissionaliza EAD</h1>", unsafe_allow_html=True)
    usuarios_df = carregar_usuarios()
    
    with st.form("login_form"):
        u = st.text_input("Utilizador").strip()
        p = st.text_input("Palavra-passe", type="password").strip()
        if st.form_submit_button("Entrar"):
            user_match = usuarios_df[usuarios_df['usuario'] == u]
            if not user_match.empty and str(user_match.iloc[0]['senha']) == p:
                st.session_state.autenticado = True
                st.session_state.usuario_ativo = u
                st.session_state.nivel_ativo = user_match.iloc[0]['nivel']
                st.rerun()
            else:
                st.error("Utilizador ou senha incorretos.")
    st.stop()

# --- 4. MENU E NAVEGAÇÃO (DESIGN ORIGINAL) ---
is_admin = st.session_state.nivel_ativo == "ADMIN"
is_consulta = st.session_state.nivel_ativo == "CONSULTA"

if is_admin:
    lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS", "👥 USUÁRIOS"]
elif is_consulta:
    lista_abas = ["🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"]
else:
    lista_abas = ["🖥️ GERENCIAMENTO"]

abas = st.tabs(lista_abas)

# Definição das variáveis das abas para evitar erros de NameError
tab_cad = tab_ger = tab_rel = tab_subir = tab_users = None

if is_admin:
    tab_cad, tab_ger, tab_rel, tab_subir, tab_users = abas[0], abas[1], abas[2], abas[3], abas[4]
elif is_consulta:
    tab_ger, tab_rel = abas[0], abas[1]
else:
    tab_ger = abas[0]

# --- ABA 1: CADASTRO (DESIGN DE CARTÕES) ---
if tab_cad:
    with tab_cad:
        st.markdown("### ✨ Registro de Nova Matrícula")
        with st.form("form_cadastro_final", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            n_id = col1.text_input("ID / Matrícula").strip()
            n_p_nome = col2.text_input("Primeiro Nome")
            n_s_nome = col3.text_input("Sobrenome")
            
            n_tel = col1.text_input("WhatsApp")
            n_cpf = col2.text_input("CPF")
            n_cid = col3.text_input("Cidade")
            
            n_cur = st.multiselect("Cursos", ["ADM", "INFORMÁTICA", "INGLÊS", "MARKETING", "RH", "LOGÍSTICA"])
            n_pag = st.selectbox("Forma de Pagamento", ["Cartão", "Boleto", "Pix", "Recorrência"])
            n_ven = st.text_input("Vendedor")
            n_ou = st.checkbox("Incluir Bônus 10 Cursos?")

            if st.form_submit_button("CADASTRAR NO BANCO"):
                if n_id and n_p_nome:
                    nome_f = formatar_nome_proprio(f"{n_p_nome} {n_s_nome}")
                    novo_aluno = {
                        "ID": n_id, "STATUS": "1", "SEC": "MGA", "TURMA": "1",
                        "10 CURSOS?": "Sim" if n_ou else "Não", "INGLÊS?": "Sim" if "INGLÊS" in n_cur else "Não",
                        "Data Cadastro": str(date.today()), "Aluno": nome_f,
                        "Tel. Aluno": n_tel, "CPF": limpar_cpf(n_cpf), "Cidade": n_cid.upper(),
                        "Curso": ", ".join(n_cur), "Pagamento": n_pag, "Vendedor": n_ven.upper(),
                        "Data Matrícula": str(date.today()), "active": "1"
                    }
                    try:
                        supabase.table("alunos").insert(novo_aluno).execute()
                        st.success("Aluno registrado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- ABA 2: GERENCIAMENTO (PESQUISA AVANÇADA) ---
if tab_ger:
    with tab_ger:
        st.header("🖥️ Gestão de Matrículas")
        col_pesq, col_btn = st.columns([3, 1])
        id_input = col_pesq.text_input("Digite o ID para pesquisar:").strip()
        
        if col_btn.button("🔍 PESQUISAR"):
            res = supabase.table("alunos").select("*").eq("ID", id_input).execute()
            if res.data:
                st.session_state.dados_aluno = res.data[0]
            else:
                st.error("Aluno não encontrado.")

        if st.session_state.dados_aluno:
            al = st.session_state.dados_aluno
            st.markdown(f"#### Editando: {al['Aluno']}")
            
            # Aqui entraria todo o seu design original de campos e botões de atualização
            with st.form("edicao_aluno"):
                e1, e2 = st.columns(2)
                up_status = e1.selectbox("Status", ["1", "0"], index=0 if al['STATUS']=="1" else 1)
                up_obs = st.text_area("Observações", value=al.get('observation', ''))
                
                if st.form_submit_button("ATUALIZAR"):
                    supabase.table("alunos").update({"STATUS": up_status, "observation": up_obs}).eq("ID", al['ID']).execute()
                    st.success("Dados atualizados!")
                    st.session_state.dados_aluno = None
                    st.rerun()

# --- ABA 3: RELATÓRIOS (DASHBOARDS ORIGINAIS) ---
if tab_rel:
    with tab_rel:
        st.header("📊 Indicadores de Desempenho")
        dados_res = supabase.table("alunos").select("STATUS, Vendedor, Pagamento").execute()
        if dados_res.data:
            df = pd.DataFrame(dados_res.data)
            
            # Métricas originais
            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Alunos", len(df))
            c2.metric("Ativos", len(df[df['STATUS']=="1"]))
            c3.metric("Cancelados", len(df[df['STATUS']=="0"]))
            
            # Gráficos (Plotly original)
            fig = px.pie(df, names='Pagamento', title="Formas de Pagamento", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

# --- ABA 5: USUÁRIOS (ADMIN) ---
if tab_users:
    with tab_users:
        st.header("👥 Gestão de Acessos")
        with st.form("novo_user"):
            u1, u2, u3 = st.columns(3)
            nu = u1.text_input("Novo Usuário")
            ns = u2.text_input("Senha")
            nv = u3.selectbox("Nível", ["ADMIN", "CONSULTA"])
            if st.form_submit_button("CRIAR"):
                supabase.table("usuarios").insert({"usuario": nu, "senha": ns, "nivel": nv}).execute()
                st.success("Usuário criado!")
                st.rerun()
        st.dataframe(carregar_usuarios(), use_container_width=True)

# --- SIDEBAR (DESIGN ORIGINAL) ---
with st.sidebar:
    st.markdown("### 🎓 Profissionaliza EAD")
    st.write(f"Logado: **{st.session_state.usuario_ativo}**")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
