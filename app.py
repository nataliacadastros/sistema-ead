import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Gestão PROFISSIONALIZA EAD", layout="wide")

# --- DICIONÁRIO DE CÓDIGOS (PRESERVADO) ---
CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- ORDEM EXATA DAS COLUNAS SOLICITADA ---
COLUNAS = [
    "STATUS", "SEC", "TURMA", "10 CURSOS?", "INGLÊS?", "Data Cadastro", 
    "ID", "Aluno", "Tel. Resp", "Tel. Aluno", "CPF", "Cidade", 
    "Curso", "Pagamento", "Vendedor", "Data Matrícula", "OBS1", "OBS2"
]

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl="0s" garante que ele sempre pegue o dado mais novo da planilha
        df = conn.read(ttl="0s")
        
        # LIMPEZA: Remove linhas que estão totalmente vazias
        df = df.dropna(how='all')
        
        # LIMPEZA EXTRA: Garante que só mostre linhas onde a coluna 'Aluno' tem conteúdo
        if 'Aluno' in df.columns:
            df = df[df['Aluno'].notna() & (df['Aluno'] != "")]
            
        return df
    except Exception as e:
        # Se der erro (ex: planilha vazia), retorna uma tabela em branco com os títulos
        return pd.DataFrame(columns=COLUNAS)

# --- INTERFACE LATERAL (MENU) ---
st.sidebar.title("MENU PRINCIPAL")
aba = st.sidebar.radio("Ir para:", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

# --- ETAPA 1: CADASTRO ---
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
            curso_cod = st.text_input("Código do Curso (Número)")
            pagamento = st.text_input("Forma de Pagamento")
            obs1 = st.text_area("OBSERVAÇÕES")
            
        if st.form_submit_button("SALVAR NO SISTEMA"):
            if not id_aluno or not nome:
                st.error("Por favor, preencha ao menos o ID e o Nome do Aluno.")
            else:
                nome_curso = CODIGOS_CURSOS.get(curso_cod, "CURSO NÃO CADASTRADO")
                
                # Lógica de colunas automáticas (Preservada)
                dez_cursos = "SIM" if curso_cod == "2" else "NÃO"
                ingles = "SIM" if curso_cod == "4" else "NÃO"
                
                # Criando o novo registro
                nova_linha = pd.DataFrame([{
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
                }])
                
                # Envia para a planilha
                dados_atuais = carregar_dados()
                df_final = pd.concat([dados_atuais, nova_linha], ignore_index=True)
                conn.update(data=df_final)
                st.success(f"Aluno {nome.upper()} salvo com sucesso na nuvem!")

# --- ETAPA 2: GERENCIAMENTO ---
elif aba == "GERENCIAMENTO":
    st.header("🔍 Consulta de Alunos")
    df_exibir = carregar_dados()
    
    if not df_exibir.empty:
        # Busca Geral
        busca = st.text_input("Pesquisar por Nome, CPF, Cidade ou Vendedor...").upper()
        if busca:
            # Filtra em todas as colunas
            mask = df_exibir.apply(lambda row: row.astype(str).str.contains(busca, na=False).any(), axis=1)
            df_exibir = df_exibir[mask]
        
        st.write(f"Exibindo {len(df_exibir)} alunos encontrados:")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado encontrado na planilha. Verifique se os cabeçalhos estão corretos.")

# --- ETAPA 3: RELATÓRIOS ---
elif aba == "RELATÓRIOS":
    st.header("📊 Resumo e Estatísticas")
    df = carregar_dados()
    
    if not df.empty:
        # Métricas Rápidas
        ativos = len(df[df["STATUS"] == "ATIVO"])
        cancelados = len(df[df["STATUS"] == "CANCELADO"])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MATRÍCULAS TOTAIS", len(df))
        c2.metric("ALUNOS ATIVOS", ativos, delta_color="normal")
        c3.metric("CANCELAMENTOS", cancelados, delta_color="inverse")
        
        st.divider()
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            # Gráfico de Vendedores (Ranking)
            st.subheader("Ranking de Vendedores")
            vendas = df["Vendedor"].value_counts().reset_index()
            fig_vend = px.bar(vendas, x="count", y="Vendedor", orientation='h', 
                             labels={'count': 'Matrículas', 'Vendedor': 'Nome'},
                             color_discrete_sequence=['#33ccff'])
            st.plotly_chart(fig_vend, use_container_width=True)
            
        with col_graf2:
            # Distribuição por Cidade
            st.subheader("Volume por Cidade")
            cidades = df["Cidade"].value_counts().reset_index()
            fig_cid = px.pie(cidades, values="count", names="Cidade", hole=0.3)
            st.plotly_chart(fig_cid, use_container_width=True)
    else:
        st.warning("Adicione alunos para visualizar os gráficos.")
