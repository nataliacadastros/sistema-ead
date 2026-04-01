import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Gestão PROFISSIONALIZA EAD", layout="wide")

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# Lista exata das suas colunas
COLUNAS = [
    "STATUS", "SEC", "TURMA", "10 CURSOS?", "INGLÊS?", "Data Cadastro", 
    "ID", "Aluno", "Tel. Resp", "Tel. Aluno", "CPF", "Cidade", 
    "Curso", "Pagamento", "Vendedor", "Data Matrícula", "OBS1", "OBS2"
]

# --- FUNÇÕES DE NUVEM (SIMULADAS PARA CONFIGURAÇÃO) ---
if "db" not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=COLUNAS)

# --- INTERFACE ---
st.sidebar.title("MENU PRINCIPAL")
aba = st.sidebar.radio("Ir para:", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    st.header("👤 Novo Cadastro")
    with st.form("form_aluno", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_aluno = st.text_input("ID")
            nome = st.text_input("Nome do Aluno")
            cpf = st.text_input("CPF Responsável")
            vendedor = st.text_input("Vendedor")
        with c2:
            tel_resp = st.text_input("Tel. Responsável")
            tel_alu = st.text_input("Tel. Aluno")
            cidade = st.text_input("Cidade")
            data_mat = st.date_input("Data Matrícula", value=date.today())
        with c3:
            curso_cod = st.text_input("Código do Curso")
            pagamento = st.text_input("Forma de Pagamento")
            obs1 = st.text_area("OBS 1")
            
        if st.form_submit_button("SALVAR NO SISTEMA"):
            nome_curso = CODIGOS_CURSOS.get(curso_cod, "CURSO NÃO CADASTRADO")
            
            # Lógica das colunas automáticas baseada no curso
            dez_cursos = "SIM" if curso_cod == "2" else "NÃO"
            ingles = "SIM" if curso_cod == "4" else "NÃO"
            
            # Criando a linha na ORDEM EXATA da sua planilha
            nova_linha = {
                "STATUS": "ATIVO",
                "SEC": "",
                "TURMA": "",
                "10 CURSOS?": dez_cursos,
                "INGLÊS?": ingles,
                "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                "ID": id_aluno,
                "Aluno": nome.upper(),
                "Tel. Resp": tel_resp,
                "Tel. Aluno": tel_alu,
                "CPF": cpf,
                "Cidade": cidade.upper(),
                "Curso": nome_curso.upper(),
                "Pagamento": pagamento.upper(),
                "Vendedor": vendedor.upper(),
                "Data Matrícula": data_mat.strftime("%d/%m/%Y"),
                "OBS1": obs1.upper(),
                "OBS2": ""
            }
            
            # Salva temporariamente (depois conectaremos à planilha real)
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nova_linha])], ignore_index=True)
            st.success(f"Aluno {nome} cadastrado com sucesso!")

elif aba == "GERENCIAMENTO":
    st.header("🔍 Consulta e Filtros")
    busca = st.text_input("Pesquisar por nome, CPF ou cidade...").upper()
    
    df_exibir = st.session_state.db
    if busca:
        df_exibir = df_exibir[df_exibir.stack().str.contains(busca).groupby(level=0).any()]
    
    st.dataframe(df_exibir, use_container_width=True)

elif aba == "RELATÓRIOS":
    st.header("📊 Resumo Operacional")
    df = st.session_state.db
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total de Matrículas", len(df))
            fig_status = px.pie(df, names="STATUS", title="Distribuição de Status", hole=0.4)
            st.plotly_chart(fig_status)
        with c2:
            st.metric("Alunos Ativos", len(df[df["STATUS"] == "ATIVO"]))
            vendas = df["Vendedor"].value_counts().reset_index()
            fig_vend = px.bar(vendas, x="count", y="Vendedor", orientation='h', title="Ranking Vendedores")
            st.plotly_chart(fig_vend)
    else:
        st.warning("Sem dados para gerar relatórios.")
