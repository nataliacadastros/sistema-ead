import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Gestão PROFISSIONALIZA EAD", layout="wide")

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a planilha em tempo real
        df = conn.read(ttl="0s")
        if df is not None:
            # Substitui todos os valores "None" ou "NaN" por um texto vazio ""
            return df.fillna("")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

# --- INTERFACE LATERAL ---
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
            obs1 = st.text_area("OBSERVAÇÕES")
            
        if st.form_submit_button("SALVAR NO SISTEMA"):
            if not nome:
                st.error("O nome do aluno é obrigatório.")
            else:
                nome_curso = CODIGOS_CURSOS.get(curso_cod, "CURSO NÃO CADASTRADO")
                nova_linha = pd.DataFrame([{
                    "STATUS": "ATIVO", "SEC": "", "TURMA": "", 
                    "10 CURSOS?": "SIM" if curso_cod == "2" else "NÃO",
                    "INGLÊS?": "SIM" if curso_cod == "4" else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": nome.upper(), "Tel. Resp": tel_resp,
                    "Tel. Aluno": tel_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": nome_curso.upper(), "Pagamento": pagamento.upper(),
                    "Vendedor": vendedor.upper(), "Data Matrícula": data_mat.strftime("%d/%m/%Y"),
                    "OBS1": obs1.upper(), "OBS2": ""
                }])
                
                # Para salvar, pegamos a planilha bruta (sem preencher com "") 
                # para manter a integridade do Google Sheets
                df_atual = conn.read(ttl="0s")
                df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                conn.update(data=df_final)
                st.success(f"Aluno {nome.upper()} cadastrado com sucesso!")

elif aba == "GERENCIAMENTO":
    st.header("🔍 Consulta de Alunos")
    df_exibir = carregar_dados()
    
    if not df_exibir.empty:
        busca = st.text_input("Pesquisar...").upper()
        if busca:
            # Filtra os dados pesquisados
            mask = df_exibir.apply(lambda row: row.astype(str).str.contains(busca, na=False).any(), axis=1)
            df_exibir = df_exibir[mask]
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

elif aba == "RELATÓRIOS":
    st.header("📊 Resumo")
    df_raw = carregar_dados()
    
    # Remove as linhas que você usa apenas para separar PDF (linhas onde o Aluno é "")
    if not df_raw.empty:
        df = df_raw[df_raw["Aluno"] != ""]
        
        if not df.empty:
            st.metric("Total de Alunos", len(df))
            c1, c2 = st.columns(2)
            with c1:
                vendas = df["Vendedor"].value_counts().reset_index()
                st.plotly_chart(px.bar(vendas, x="count", y="Vendedor", orientation='h', title="Ranking de Vendedores"))
            with c2:
                status = df["STATUS"].value_counts().reset_index()
                st.plotly_chart(px.pie(status, values="count", names="STATUS", title="Status"))
