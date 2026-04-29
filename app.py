import streamlit as st
import pandas as pd
import re
from datetime import date

# Configuração da página
st.set_page_config(page_title="Gestão de Alunos", layout="centered")

# Inicialização do estado da sessão
if 'pre_visualizacao' not in st.session_state:
    st.session_state.pre_visualizacao = []
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = []

# Tabela de Conversão Atualizada
CURSOS_MAP = {
    "00": "COLÉGIO COMBO",
    "0": "COLÉGIO COMBO",
    "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS",
    "5": "JOVEM NO DIREITO",
    "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA",
    "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA",
    "10": "ADMINISTRAÇÃO"
}

def converter_curso(texto):
    if not texto:
        return ""
    
    # Busca por números no final da frase (ex: "Combo 4" -> acha "4")
    match = re.search(r'(\d+)$', texto.strip())
    
    if match:
        codigo = match.group(1)
        # Se o código existe na nossa tabela
        if codigo in CURSOS_MAP or str(int(codigo)) in CURSOS_MAP:
            nome_curso = CURSOS_MAP.get(codigo) or CURSOS_MAP.get(str(int(codigo)))
            # Substitui o número pelo nome do curso mantendo o que veio antes
            novo_texto = texto[:match.start()] + nome_curso
            return novo_texto.upper()
    
    return texto.upper()

st.title("🚀 Gestão de Alunos")

tab1, tab2 = st.tabs(["📝 Cadastro", "📊 Gerenciamento"])

with tab1:
    st.header("Cadastro de Aluno")
    
    id_aluno = st.text_input("ID")
    nome = st.text_input("ALUNO")
    tel_resp = st.text_input("TEL. RESPONSÁVEL")
    tel_aluno = st.text_input("TEL. ALUNO")
    cpf = st.text_input("CPF RESPONSÁVEL", placeholder="000.000.000-00")
    cidade = st.text_input("CIDADE")
    
    # Campo CURSO com a nova lógica de sufixo
    curso_raw = st.text_input("CURSO CONTRATADO", help="Digite o texto e o código no final (ex: Combo 4)")
    curso_nome = converter_curso(curso_raw)
    
    if curso_nome != curso_raw.upper() and curso_raw != "":
        st.info(f"✨ Convertido para: **{curso_nome}**")

    vendedor = st.text_input("VENDEDOR")
    data_mat = st.date_input("DATA DA MATRÍCULA", value=date.today())
    
    forma_pagto_base = st.text_input("FORMA DE PAGAMENTO")

    st.write("---")
    c_lib = st.checkbox("☑ LIB. IN-GLÊS")
    c_bonus = st.checkbox("☑ CURSO BÔNUS")
    c_conf = st.checkbox("☑ CONFIRMAÇÃO")

    # Lógica de concatenação
    obs = []
    if c_lib: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if c_bonus: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if c_conf: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    
    texto_pagamento_final = forma_pagto_base.upper()
    if obs:
        if texto_pagamento_final:
            texto_pagamento_final += " | " + " | ".join(obs)
        else:
            texto_pagamento_final = " | ".join(obs)

    st.write("---")
    if st.button("💾 SALVAR ALUNO"):
        novo_aluno = {
            "ID": id_aluno,
            "ALUNO": nome.upper(),
            "TEL. RESPONSÁVEL": tel_resp,
            "TEL. ALUNO": tel_aluno,
            "CPF": cpf,
            "CIDADE": cidade.upper(),
            "CURSO": curso_nome,
            "PAGAMENTO": texto_pagamento_final,
            "VENDEDOR": vendedor.upper(),
            "DATA": data_mat.strftime("%d/%m/%Y")
        }
        st.session_state.pre_visualizacao.append(novo_aluno)
        st.toast("Aluno adicionado à lista!")

    if st.session_state.pre_visualizacao:
        st.subheader("📋 PRÉ-VISUALIZAÇÃO")
        st.table(pd.DataFrame(st.session_state.pre_visualizacao))
        
        if st.button("📤 Enviar todos para Gerenciamento"):
            st.session_state.banco_dados.extend(st.session_state.pre_visualizacao)
            st.session_state.pre_visualizacao = [] 
            st.rerun()

with tab2:
    st.header("Base de Dados")
    if st.session_state.banco_dados:
        df_final = pd.DataFrame(st.session_state.banco_dados)
        st.dataframe(df_final, use_container_width=True)
