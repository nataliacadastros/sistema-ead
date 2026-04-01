<style>
    /* 1. Reduz a altura do container do input e do input em si */
    div[data-testid="stTextInput"] > div {
        min-height: 20px !important;
        height: 20px !important;
        margin-bottom: 2px !important;
    }

    .stTextInput>div>div>input { 
        background-color: white !important; 
        color: black !important; 
        height: 20px !important; /* Altura real do campo */
        min-height: 20px !important;
        line-height: 20px !important;
        text-transform: uppercase !important; 
        border-radius: 2px !important; 
        font-size: 11px !important;
        padding: 0px 5px !important; /* Remove respiro interno superior/inferior */
    }

    /* 2. Gruda o label no input */
    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 10px !important; 
        margin-bottom: -15px !important; /* Puxa o input para cima do label */
        display: block;
    }

    /* 3. Tira o espaço entre um campo e outro */
    [data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
        margin-bottom: -10px !important; /* Ajuste fino para empilhar */
    }
</style>
