# --- ABA 5: USUÁRIOS (ADMIN) ---
if is_admin:
    with tab_users:
        st.markdown("### 👥 GESTÃO DE ACESSOS")
        
        # Formulário para cadastrar
        with st.form("novo_user_form", clear_on_submit=True):
            col_u, col_p, col_n = st.columns(3)
            nu_user = col_u.text_input("Novo Usuário").strip()
            nu_pass = col_p.text_input("Senha").strip()
            nu_nivel = col_n.selectbox("Nível", ["ADMIN", "CONSULTA"])
            
            if st.form_submit_button("CADASTRAR NOVO ACESSO"):
                if nu_user and nu_pass:
                    try:
                        # Pegamos as credenciais dos secrets
                        creds_info = st.secrets["connections"]["gsheets"]
                        
                        # DEFINIÇÃO DOS ESCOPOS (Resolve o erro de Invalid OAuth scope)
                        scopes = [
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                        
                        # Autorização com os escopos corretos
                        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
                        client = gspread.authorize(credentials)
                        
                        # Tenta abrir a planilha e a aba usuários
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        ws_u = sh.worksheet("usuários")
                        
                        # Salva os dados
                        ws_u.append_row([nu_user, nu_pass, nu_nivel])
                        
                        st.success(f"Usuário {nu_user} cadastrado com sucesso!")
                        st.cache_data.clear() # Limpa o cache para atualizar a tabela abaixo
                    except Exception as e:
                        st.error(f"Erro ao salvar na planilha: {e}")
                else:
                    st.warning("Preencha usuário e senha.")

        st.write("---")
        st.markdown("#### 📋 Usuários Cadastrados")
        
        # Botão para forçar atualização manual
        if st.button("🔄 ATUALIZAR LISTA DE USUÁRIOS"):
            st.cache_data.clear()
            st.rerun()

        # Chamada da função que lê os usuários
        df_usuarios_ver = carregar_usuarios()
        
        if not df_usuarios_ver.empty:
            st.dataframe(
                df_usuarios_ver, 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Nenhum usuário encontrado na aba 'usuários'. Verifique se existem dados na planilha ou se o cabeçalho está correto.")
