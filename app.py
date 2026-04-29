import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from openpyxl import Workbook
from io import BytesIO
from supabase import create_client

# --- 1. CONFIGURAÇÕES INICIAIS & DESIGN ---
st.set_page_config(page_title="Sistema Unificado - Profissionaliza EAD", layout="wide", page_icon="🎓")

# Estilização CSS para o design moderno (Cards e Botões)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        width: 100%;
        border: none;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #0056b3;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO SUPABASE ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Erro Crítico: Chaves do Supabase não encontradas nos Secrets.")
    st.stop()

# --- 3. LÓGICA DE DADOS & FUNÇÕES AUXILIARES ---

def carregar_usuarios():
    try:
        response = supabase.table("usuarios").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=["usuario", "senha", "nivel"])
    except:
        return pd.DataFrame(columns=["usuario", "senha", "nivel"])

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf))

def formatar_nome_proprio(nome):
    preposicoes = {'Da', 'De', 'Di', 'Do', 'Du', 'Dos', 'Das'}
    palavras = nome.title().split()
    return " ".join([p if p not in preposicoes else p.lower() for p in palavras])

# --- 4. SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_ativo = ""
    st.session_state.nivel_ativo = ""
if 'dados_aluno' not in st.session_state:
    st.session_state.dados_aluno = None

if not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.title("🔐 Acesso Restrito")
        usuarios_df = carregar_usuarios()
        
        with st.form("login_form"):
            user_input = st.text_input("Usuário").strip()
            pass_input = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                user_data = usuarios_df[usuarios_df['usuario'] == user_input]
                if not user_data.empty and str(user_data.iloc[0]['senha']) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_ativo = user_input
                    st.session_state.nivel_ativo = user_data.iloc[0]['nivel']
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. NAVEGAÇÃO E ABAS ---
is_admin = st.session_state.nivel_ativo == "ADMIN"
lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "👥 CONFIGURAÇÕES"] if is_admin else ["🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"]
tabs = st.tabs(lista_abas)

# --- 6. ABA 1: CADASTRO COMPLETO ---
if is_admin:
    with tabs[0]:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.header("✨ Novo Registro de Aluno")
        
        with st.form("form_cadastro_completo", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            f_id = c1.text_input("ID / Matrícula").strip()
            f_p_nome = c2.text_input("Primeiro Nome").strip()
            f_s_nome = c3.text_input("Sobrenome").strip()
            
            f_cpf = c1.text_input("CPF (Somente números)")
            f_tel = c2.text_input("WhatsApp com DDD")
            f_cid = c3.text_input("Cidade")
            
            f_cur = st.multiselect("Cursos Contratados", ["ADM", "INFORMÁTICA", "INGLÊS", "MARKETING", "RH", "LOGÍSTICA"])
            f_pag = st.selectbox("Forma de Pagamento", ["Cartão", "Boleto", "Pix", "Recorrência", "Grátis"])
            f_ven = st.text_input("Vendedor / Atendente")
            f_obs = st.text_area("Observações Adicionais")
            
            f_bonus = st.checkbox("Liberar Bônus 10 Cursos?")
            
            if st.form_submit_button("CONFIRMAR MATRÍCULA"):
                if f_id and f_p_nome and f_cpf:
                    # Preparação dos dados exata para o Supabase
                    nome_completo = formatar_nome_proprio(f"{f_p_nome} {f_s_nome}")
                    email_fake = f"{f_p_nome.lower()}.{f_id}@profissionalizaead.com.br"
                    tags_cursos = ", ".join(f_cur)
                    
                    dados_aluno = {
                        "ID": f_id,
                        "STATUS": "ATIVO",
                        "SEC": "MGA",
                        "TURMA": "1",
                        "10 CURSOS?": "Sim" if f_bonus else "Não",
                        "INGLÊS?": "Sim" if "INGLÊS" in f_cur else "Não",
                        "Data Cadastro": str(date.today()),
                        "Aluno": nome_completo,
                        "Tel. Resp": f_tel,
                        "Tel. Aluno": f_tel,
                        "CPF": limpar_cpf(f_cpf),
                        "Cidade": f_cid.upper(),
                        "Curso": tags_cursos,
                        "Pagamento": f_pag,
                        "Vendedor": f_ven.upper(),
                        "Data Matrícula": str(date.today()),
                        "observation": f_obs
                    }
                    
                    try:
                        supabase.table("alunos").insert(dados_aluno).execute()
                        st.success(f"Matrícula de {f_p_nome} realizada com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                else:
                    st.error("Campos obrigatórios: ID, Nome e CPF.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. ABA 2: GERENCIAMENTO (PESQUISA E EDIÇÃO) ---
with (tabs[1] if is_admin else tabs[0]):
    st.header("📋 Gestão e Edição de Matrículas")
    
    # Campo de busca profissional
    col_s1, col_s2 = st.columns([4, 1])
    search_id = col_s1.text_input("🔍 Digite o ID do Aluno para editar:", key="search_main").strip()
    
    if col_s2.button("BUSCAR", use_container_width=True):
        try:
            res = supabase.table("alunos").select("*").eq("ID", search_id).execute()
            if res.data:
                st.session_state.dados_aluno = res.data[0]
                st.success("Registro localizado com sucesso!")
            else:
                st.error("ID não encontrado no Banco de Dados.")
        except Exception as e:
            st.error(f"Erro na conexão: {e}")

    # Formulário de Edição (Só aparece se encontrar o aluno)
    if st.session_state.dados_aluno:
        al = st.session_state.dados_aluno
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader(f"📝 Editando: {al['Aluno']}")
        
        with st.form("form_edit"):
            e1, e2, e3 = st.columns(3)
            up_status = e1.selectbox("Status Atual", ["ATIVO", "CANCELADO", "PENDENTE"], index=0 if al['STATUS'] == "ATIVO" else 1)
            up_pag = e2.selectbox("Pagamento", ["Cartão", "Boleto", "Pix", "Recorrência"], index=0)
            up_tel = e3.text_input("Telefone", value=al['Tel. Aluno'])
            
            up_obs = st.text_area("Histórico / Observações", value=al.get('observation', ''))
            
            col_eb1, col_eb2 = st.columns(2)
            if col_eb1.form_submit_button("SALVAR ALTERAÇÕES"):
                try:
                    supabase.table("alunos").update({
                        "STATUS": up_status,
                        "Pagamento": up_pag,
                        "Tel. Aluno": up_tel,
                        "Tel. Resp": up_tel,
                        "observation": up_obs
                    }).eq("ID", al['ID']).execute()
                    st.success("Dados atualizados instantaneamente!")
                    st.session_state.dados_aluno = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
            
            if col_eb2.form_submit_button("CANCELAR EDIÇÃO"):
                st.session_state.dados_aluno = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 8. ABA 3: RELATÓRIOS E DASHBOARD ---
with (tabs[2] if is_admin else tabs[1]):
    st.header("📊 Inteligência de Dados")
    
    try:
        # Puxa todos os dados para o Dashboard (O Supabase é muito rápido aqui)
        res_all = supabase.table("alunos").select("STATUS, Vendedor, Pagamento, Data Matrícula").execute()
        if res_all.data:
            df = pd.DataFrame(res_all.data)
            
            # Métricas principais
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Matrículas", len(df))
            m2.metric("Alunos Ativos", len(df[df['STATUS'] == "ATIVO"]))
            m3.metric("Cancelados", len(df[df['STATUS'] == "CANCELADO"]))
            m4.metric("Vendedores Ativos", df['Vendedor'].nunique())
            
            st.divider()
            
            # Gráficos Dinâmicos
            g1, g2 = st.columns(2)
            with g1:
                fig_pag = px.pie(df, names='Pagamento', title="📌 Vendas por Forma de Pagamento", hole=0.4)
                st.plotly_chart(fig_pag, use_container_width=True)
            
            with g2:
                vendas_vendedor = df['Vendedor'].value_counts().reset_index()
                fig_ven = px.bar(vendas_vendedor, x='index', y='Vendedor', title="🏆 Ranking de Vendedores", color='Vendedor')
                st.plotly_chart(fig_ven, use_container_width=True)
        else:
            st.warning("Aguardando os primeiros registros para gerar gráficos.")
    except:
        st.error("Não foi possível carregar o dashboard.")

# --- 9. ABA 4: CONFIGURAÇÕES (GESTÃO DE USUÁRIOS) ---
if is_admin:
    with tabs[3]:
        st.header("⚙️ Painel de Controle Administrativo")
        
        # Gestão de Usuários do Sistema
        with st.expander("👥 Gerenciar Acessos ao Sistema"):
            with st.form("novo_user_sys"):
                u1, u2, u3 = st.columns(3)
                new_u = u1.text_input("Novo Usuário").strip()
                new_s = u2.text_input("Senha Temporária").strip()
                new_n = u3.selectbox("Nível de Permissão", ["ADMIN", "CONSULTA"])
                
                if st.form_submit_button("CRIAR ACESSO"):
                    if new_u and new_s:
                        supabase.table("usuarios").insert({"usuario": new_u, "senha": new_s, "nivel": new_n}).execute()
                        st.success("Usuário criado com sucesso!")
                        st.rerun()
            
            st.write("### Usuários Atuais")
            st.dataframe(carregar_usuarios(), use_container_width=True)

        # Backup de Segurança
        st.divider()
        st.subheader("📥 Backup de Dados")
        if st.button("GERAR ARQUIVO EXCEL COMPLETO"):
            res_backup = supabase.table("alunos").select("*").execute()
            df_back = pd.DataFrame(res_backup.data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_back.to_excel(writer, index=False, sheet_name='Alunos')
            st.download_button(label="CLIQUE PARA BAIXAR BACKUP", data=output.getvalue(), file_name=f"BACKUP_EAD_{date.today()}.xlsx")

# --- 10. SIDEBAR (LOGOUT) ---
with st.sidebar:
    st.markdown(f"### Bem-vinda, **{st.session_state.usuario_ativo}**")
    st.write(f"Nível: `{st.session_state.nivel_ativo}`")
    st.divider()
    if st.button("SAIR DO SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()
    st.info("Sistema operando em Banco de Dados SQL (Supabase).")
