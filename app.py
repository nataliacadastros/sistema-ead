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
st.set_page_config(page_title="SISTEMA UNIFICADO - Profissionaliza EAD", layout="wide", page_icon="🎓")

ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

# --- CONEXÃO SUPABASE (ÚNICA) ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro de conexão com o Banco de Dados: {e}")
    st.stop()

# --- 2. FUNÇÕES DE SUPORTE (LOGICA ORIGINAL) ---

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

# --- 3. LÓGICA DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_ativo = ""
    st.session_state.nivel_ativo = ""
if 'dados_aluno' not in st.session_state:
    st.session_state.dados_aluno = None

if not st.session_state.autenticado:
    st.title("🔐 Login - Profissionaliza EAD")
    df_u = carregar_usuarios()
    with st.form("login"):
        u = st.text_input("Usuário").strip()
        p = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("Entrar"):
            user_match = df_u[df_u['usuario'] == u]
            if not user_match.empty and str(user_match.iloc[0]['senha']) == p:
                st.session_state.autenticado = True
                st.session_state.usuario_ativo = u
                st.session_state.nivel_ativo = user_match.iloc[0]['nivel']
                st.rerun()
            else:
                st.error("Incorreto.")
    st.stop()

# --- 4. INTERFACE PRINCIPAL (ABAS DINÂMICAS) ---
is_admin = st.session_state.nivel_ativo == "ADMIN"
is_consulta = st.session_state.nivel_ativo == "CONSULTA"

if is_admin:
    lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS", "👥 USUÁRIOS"]
elif is_consulta:
    lista_abas = ["🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"]
else:
    lista_abas = ["🖥️ GERENCIAMENTO"]

abas = st.tabs(lista_abas)

# Mapeamento para não dar erro de NameError
tab_cad = tab_ger = tab_rel = tab_subir = tab_users = None
if is_admin:
    tab_cad, tab_ger, tab_rel, tab_subir, tab_users = abas[0], abas[1], abas[2], abas[3], abas[4]
elif is_consulta:
    tab_ger, tab_rel = abas[0], abas[1]
else:
    tab_ger = abas[0]

# --- ABA 1: CADASTRO ---
if tab_cad:
    with tab_cad:
        st.header("✨ Novo Cadastro Individual")
        with st.form("form_cad", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n_id = c1.text_input("ID Aluno (Matrícula)").strip()
            n_p_nome = c2.text_input("Primeiro Nome")
            n_s_nome = c3.text_input("Sobrenome")
            
            n_tel = c1.text_input("WhatsApp (DDD + Número)")
            n_cpf = c2.text_input("CPF")
            n_cid = c3.selectbox("Cidade", carregar_cidades()['Cidade'].tolist() if not carregar_cidades().empty else ["Maringá"])
            
            n_cur = st.multiselect("Cursos", ["ADM", "INFO", "INGLÊS", "MARKETING", "RH"])
            n_pag = st.selectbox("Pagamento", ["Cartão", "Boleto", "Pix", "Grátis"])
            n_ven = st.text_input("Vendedor")
            n_obs = st.text_area("Observações")
            n_ou = st.checkbox("Bônus Ouro?")

            if st.form_submit_button("FINALIZAR MATRÍCULA"):
                if n_id and n_p_nome:
                    nome_formatado = formatar_nome_proprio(f"{n_p_nome} {n_s_nome}")
                    dados = {
                        "ID": n_id, "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "1",
                        "10 CURSOS?": "Sim" if n_ou else "Não", "INGLÊS?": "Sim" if "INGLÊS" in n_cur else "Não",
                        "Data Cadastro": str(date.today()), "Aluno": nome_formatado,
                        "Tel. Resp": n_tel, "Tel. Aluno": n_tel, "CPF": limpar_cpf(n_cpf),
                        "Cidade": n_cid, "Curso": ", ".join(n_cur), "Pagamento": n_pag,
                        "Vendedor": n_ven.upper(), "Data Matrícula": str(date.today()), "observation": n_obs
                    }
                    try:
                        supabase.table("alunos").insert(dados).execute()
                        st.success("Salvo no Supabase!")
                        st.balloons()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO (PESQUISA SQL) ---
if tab_ger:
    with tab_ger:
        st.header("📋 Gerenciar Matrículas")
        cp1, cp2 = st.columns([3, 1])
        id_b = cp1.text_input("ID do Aluno para editar:", key="id_edit").strip()
        
        if cp2.button("🔍 PESQUISAR"):
            try:
                res = supabase.table("alunos").select("*").eq("ID", id_b).execute()
                if res.data:
                    st.session_state.dados_aluno = res.data[0]
                    st.success("Localizado!")
                else: st.error("Não encontrado.")
            except Exception as e: st.error(f"Erro: {e}")

        if st.session_state.dados_aluno:
            al = st.session_state.dados_aluno
            with st.form("edicao"):
                st.subheader(f"Editando: {al['Aluno']}")
                e1, e2 = st.columns(2)
                novo_status = e1.selectbox("Status", ["ATIVO", "CANCELADO", "PENDENTE"], index=0 if al['STATUS']=="ATIVO" else 1)
                novo_tel = e2.text_input("Telefone", value=al['Tel. Aluno'])
                nova_obs = st.text_area("Observações", value=al.get('observation', ''))
                
                if st.form_submit_button("ATUALIZAR"):
                    try:
                        supabase.table("alunos").update({
                            "STATUS": novo_status, "Tel. Aluno": novo_tel, "observation": nova_obs
                        }).eq("ID", al['ID']).execute()
                        st.success("Atualizado!")
                        st.session_state.dados_aluno = None
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS (DASHBOARD ANALÍTICO) ---
if tab_rel:
    with tab_rel:
        st.header("📊 Dashboard de Performance")
        try:
            res = supabase.table("alunos").select("STATUS, Pagamento, Vendedor, Data Matrícula").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                col1, col2, col3 = st.columns(3)
                col1.metric("Total", len(df))
                col2.metric("Ativos", len(df[df['STATUS']=="ATIVO"]))
                col3.metric("Faturamento (Simulado)", f"R$ {len(df)*150}")
                
                fig = px.bar(df['Vendedor'].value_counts().reset_index(), x='index', y='Vendedor', title="Vendas por Vendedor")
                st.plotly_chart(fig, use_container_width=True)
        except: st.warning("Sem dados.")

# --- ABA 4: SUBIR EM LOTE ---
if tab_subir and is_admin:
    with tab_subir:
        st.header("📤 Importação via CSV")
        u_file = st.file_uploader("Arraste o arquivo BANCO_EAD.csv", type="csv")
        if u_file:
            df_lote = pd.read_csv(u_file)
            if st.button("PROCESSAR LOTE PARA SUPABASE"):
                progress = st.progress(0)
                try:
                    for i, row in df_lote.iterrows():
                        d_lote = row.to_dict()
                        supabase.table("alunos").insert(d_lote).execute()
                        progress.progress((i+1)/len(df_lote))
                    st.success("Lote importado!")
                except Exception as e: st.error(f"Erro no lote: {e}")

# --- ABA 5: USUÁRIOS ---
if tab_users and is_admin:
    with tab_users:
        st.header("👥 Gestão de Acessos")
        with st.form("new_user"):
            u1, u2, u3 = st.columns(3)
            nu = u1.text_input("Novo Usuário")
            ns = u2.text_input("Senha")
            nv = u3.selectbox("Nível", ["ADMIN", "CONSULTA"])
            if st.form_submit_button("Cadastrar"):
                supabase.table("usuarios").insert({"usuario": nu, "senha": ns, "nivel": nv}).execute()
                st.success("Ok!")
                st.rerun()
        st.dataframe(carregar_usuarios(), use_container_width=True)

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"Conectado: **{st.session_state.usuario_ativo}**")
    if st.button("Logout"):
        st.session_state.autenticado = False
        st.rerun()
