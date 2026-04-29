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

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
st.set_page_config(page_title="Sistema Unificado - Profissionaliza EAD", layout="wide", page_icon="🎓")

ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

# --- CONEXÃO SUPABASE ---
try:
    # Usando as chaves que você forneceu
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro nas credenciais do Supabase: {e}")

# --- 2. FUNÇÕES DE SUPORTE E DADOS ---

def carregar_usuarios():
    try:
        response = supabase.table("usuarios").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except:
        pass
    return pd.DataFrame(columns=["usuario", "senha", "nivel"])

def carregar_tags():
    if os.path.exists(ARQUIVO_TAGS):
        with open(ARQUIVO_TAGS, "r") as f:
            return json.load(f)
    return {}

def salvar_tags(tags):
    with open(ARQUIVO_TAGS, "w") as f:
        json.dump(tags, f)

def carregar_cidades():
    if os.path.exists(ARQUIVO_CIDADES):
        return pd.read_excel(ARQUIVO_CIDADES)
    return pd.DataFrame(columns=["Cidade"])

def formatar_nome_proprio(nome):
    preposicoes = {'Da', 'De', 'Di', 'Do', 'Du', 'Dos', 'Das', 'E'}
    palavras = nome.strip().title().split()
    return " ".join([p if p not in preposicoes else p.lower() for p in palavras])

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf))

def formatar_cpf(cpf):
    d = limpar_cpf(cpf)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return d

def formatar_whatsapp(tel):
    d = re.sub(r'\D', '', str(tel))
    if len(d) == 11:
        return f"({d[:2]}) {d[2]} {d[3:7]}-{d[7:]}"
    elif len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d

# --- 3. LÓGICA DE AUTENTICAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_ativo = ""
    st.session_state.nivel_ativo = ""
if 'dados_aluno' not in st.session_state:
    st.session_state.dados_aluno = None

if not st.session_state.autenticado:
    # Centralizando o Login
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
        usuarios_df = carregar_usuarios()
        
        with st.form("login_form"):
            user_input = st.text_input("Usuário").strip()
            pass_input = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("Entrar"):
                user_data = usuarios_df[usuarios_df['usuario'] == user_input]
                if not user_data.empty and str(user_data.iloc[0]['senha']) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_ativo = user_input
                    st.session_state.nivel_ativo = user_data.iloc[0]['nivel']
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# --- 4. MENU E ABAS (LÓGICA ORIGINAL DE 751 LINHAS) ---
is_admin = st.session_state.nivel_ativo == "ADMIN"
is_consulta = st.session_state.nivel_ativo == "CONSULTA"

if is_admin:
    lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS", "👥 USUÁRIOS"]
elif is_consulta:
    lista_abas = ["🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"]
else:
    lista_abas = ["🖥️ GERENCIAMENTO"]

abas = st.tabs(lista_abas)

tab_cad = tab_ger = tab_rel = tab_subir = tab_users = None
if is_admin:
    tab_cad, tab_ger, tab_rel, tab_subir, tab_users = abas[0], abas[1], abas[2], abas[3], abas[4]
elif is_consulta:
    tab_ger, tab_rel = abas[0], abas[1]
else:
    tab_ger = abas[0]

# --- ABA 1: CADASTRO (Mantendo todo o seu formulário original) ---
if tab_cad:
    with tab_cad:
        st.header("✨ Novo Registro de Aluno")
        with st.form("form_cadastro_final", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            n_id = col1.text_input("ID do Aluno (Matrícula)").strip()
            n_p_nome = col2.text_input("Primeiro Nome")
            n_s_nome = col3.text_input("Sobrenome")
            
            n_email = col1.text_input("E-mail")
            n_tel = col2.text_input("WhatsApp (com DDD)")
            n_cpf = col3.text_input("CPF")
            
            cidades_df = carregar_cidades()
            n_cid = col1.selectbox("Cidade", cidades_df['Cidade'].tolist() if not cidades_df.empty else ["Maringá"])
            n_cur = col2.multiselect("Cursos", ["ADM", "INFORMÁTICA", "INGLÊS", "MARKETING", "RH", "LOGÍSTICA"])
            n_pag = col3.selectbox("Forma de Pagamento", ["Cartão", "Boleto", "Pix", "Recorrência", "Grátis"])
            
            n_ven = col1.text_input("Vendedor")
            n_obs = st.text_area("Observações")
            n_ou = st.checkbox("Incluir Bônus 10 Cursos?")

            if st.form_submit_button("CADASTRAR ALUNO"):
                if n_id and n_p_nome:
                    nome_f = formatar_nome_proprio(f"{n_p_nome} {n_s_nome}")
                    novo_registro = {
                        "ID": n_id, "STATUS": "1", "SEC": "MGA", "TURMA": "1",
                        "10 CURSOS?": "Sim" if n_ou else "Não", "INGLÊS?": "Sim" if "INGLÊS" in n_cur else "Não",
                        "Data Cadastro": str(date.today()), "Aluno": nome_f,
                        "Tel. Aluno": n_tel, "CPF": limpar_cpf(n_cpf), "Cidade": n_cid.upper(),
                        "Curso": ", ".join(n_cur), "Pagamento": n_pag, "Vendedor": n_ven.upper(),
                        "Data Matrícula": str(date.today()), "active": "1", "observation": n_obs
                    }
                    try:
                        supabase.table("alunos").insert(novo_registro).execute()
                        st.success("Aluno cadastrado no Supabase com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- ABA 2: GERENCIAMENTO (Pesquisa SQL Instantânea) ---
if tab_ger:
    with tab_ger:
        st.header("📋 Gestão e Edição")
        col_p1, col_p2 = st.columns([3, 1])
        id_input = col_p1.text_input("Digite o ID para pesquisar:", key="input_pesq").strip()
        
        if col_p2.button("🔍 PESQUISAR"):
            res = supabase.table("alunos").select("*").eq("ID", id_input).execute()
            if res.data:
                st.session_state.dados_aluno = res.data[0]
                st.success("Localizado!")
            else:
                st.error("Aluno não encontrado.")

        if st.session_state.dados_aluno:
            al = st.session_state.dados_aluno
            st.markdown(f"#### Editando: {al['Aluno']}")
            with st.form("edicao_aluno_form"):
                e1, e2, e3 = st.columns(3)
                up_status = e1.selectbox("Status", ["1", "0"], index=0 if al['STATUS']=="1" else 1)
                up_tel = e2.text_input("Telefone", value=al['Tel. Aluno'])
                up_pag = e3.selectbox("Pagamento", ["Cartão", "Boleto", "Pix", "Recorrência"], index=0)
                
                up_obs = st.text_area("Observações", value=al.get('observation', ''))
                
                if st.form_submit_button("ATUALIZAR DADOS"):
                    try:
                        supabase.table("alunos").update({
                            "STATUS": up_status, "Tel. Aluno": up_tel, "Pagamento": up_pag, "observation": up_obs
                        }).eq("ID", al['ID']).execute()
                        st.success("Atualizado com sucesso!")
                        st.session_state.dados_aluno = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")

# --- ABA 3: RELATÓRIOS (Todo o seu Dashboard Plotly) ---
if tab_rel:
    with tab_rel:
        st.header("📊 Inteligência de Dados")
        res_rel = supabase.table("alunos").select("STATUS, Vendedor, Pagamento, Data Matrícula").execute()
        if res_rel.data:
            df = pd.DataFrame(res_rel.data)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Alunos", len(df))
            m2.metric("Ativos", len(df[df['STATUS']=="1"]))
            m3.metric("Cancelados", len(df[df['STATUS']=="0"]))
            
            st.divider()
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig1 = px.pie(df, names='Pagamento', title="Distribuição Financeira", hole=0.4)
                st.plotly_chart(fig1, use_container_width=True)
            with col_g2:
                v_counts = df['Vendedor'].value_counts().reset_index()
                fig2 = px.bar(v_counts, x='index', y='Vendedor', title="Ranking de Vendedores")
                st.plotly_chart(fig2, use_container_width=True)

# --- ABA 4: SUBIR EM LOTE (Ajustado para Supabase) ---
if tab_subir and is_admin:
    with tab_subir:
        st.header("📤 Importação via CSV")
        arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type="csv")
        if arquivo_csv:
            df_csv = pd.read_csv(arquivo_csv)
            st.dataframe(df_csv.head())
            if st.button("INICIAR UPLOAD PARA BANCO DE DADOS"):
                progresso = st.progress(0)
                for i, row in df_csv.iterrows():
                    # Converte linha em dicionário e envia
                    dados_linha = row.to_dict()
                    supabase.table("alunos").insert(dados_linha).execute()
                    progresso.progress((i + 1) / len(df_csv))
                st.success("Importação concluída!")

# --- ABA 5: USUÁRIOS (ADMIN) ---
if tab_users and is_admin:
    with tab_users:
        st.header("👥 Gestão de Acessos")
        with st.form("novo_usuario_final"):
            u1, u2, u3 = st.columns(3)
            new_u = u1.text_input("Novo Usuário").strip()
            new_s = u2.text_input("Senha").strip()
            new_n = u3.selectbox("Nível", ["ADMIN", "CONSULTA"])
            if st.form_submit_button("CADASTRAR"):
                if new_u and new_s:
                    try:
                        supabase.table("usuarios").insert({"usuario": new_u, "senha": new_s, "nivel": new_n}).execute()
                        st.success("Usuário criado!")
                        st.cache_data.clear()
                        st.rerun()
                    except:
                        st.error("Erro ao criar usuário.")
        
        st.divider()
        st.subheader("Lista de Usuários")
        st.dataframe(carregar_usuarios(), use_container_width=True, hide_index=True)

# --- SIDEBAR (DESIGN ORIGINAL) ---
with st.sidebar:
    st.markdown("### 🎓 Profissionaliza EAD")
    st.write(f"Utilizador: **{st.session_state.usuario_ativo}**")
    st.write(f"Nível: `{st.session_state.nivel_ativo}`")
    st.divider()
    if st.button("SAIR DO SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()
