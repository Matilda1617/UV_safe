import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns

# Configurazione della pagina
st.set_page_config(
    page_title="UV-Safe: Raggi UV e Verde Urbano",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Regole CSS: Contrasti elevati, palette naturale e rimozione del tasto Deploy
st.markdown("""
<style>
    .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background-color: #ffffff;
        color: #111111;
    }
    
    h1, h2, h3, h4 {
        color: #1b5e20;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    [data-testid="stMetricValue"] {
        color: #111111 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #37474f !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    .stDownloadButton > button {
        background-color: #f5efe6 !important;
        color: #1b1b1b !important;
        border: 2px solid #5d4037 !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        border-radius: 4px !important;
        transition: all 0.2s ease-in-out;
    }
    .stDownloadButton > button:hover {
        background-color: #5d4037 !important;
        color: #ffffff !important;
        border: 2px solid #3e2723 !important;
    }

    .box-sabbia {
        background-color: #f5efe6;
        border-left: 5px solid #6d4c41;
        border-radius: 4px;
        padding: 16px 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        color: #111111;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .box-bosco {
        background-color: #edf5ee;
        border-left: 5px solid #2e7d32;
        border-radius: 4px;
        padding: 16px 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        color: #111111;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .box-ardesia {
        background-color: #f0f2f5;
        border-left: 5px solid #37474f;
        border-radius: 4px;
        padding: 16px 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        color: #111111;
        font-size: 15px;
        line-height: 1.6;
    }

    .tabella-naturale {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 14px;
        color: #111111;
    }
    .tabella-naturale th {
        background-color: #e2dcd5;
        color: #2b1d0c;
        padding: 12px 14px;
        border: 1px solid #bcaaa4;
        text-align: left;
        font-weight: 700;
    }
    .tabella-naturale td {
        padding: 10px 14px;
        border: 1px solid #d7ccc8;
        background-color: #ffffff;
    }
    .tabella-naturale tr:nth-child(even) td {
        background-color: #fbf9f6;
    }

    .divisore-naturale {
        border-top: 2px solid #b0bec5;
        margin-top: 25px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

DATA_PATH = "dataset/processed/uv_verde_unificato_2024.csv"
GRAPH_PATH = "output/uv_safe_graph.ttl"

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df_in = pd.read_csv(DATA_PATH, sep=";")
        
        def pulisci_nome_comune(nome):
            if pd.isna(nome):
                return ""
            s = str(nome).strip()
            s = s.replace("'''", "'").replace("''", "'")
            if "bolzano" in s.lower():
                return "Bolzano"
            if "aquila" in s.lower() or "aquilda" in s.lower():
                return "L'Aquila"
            if "reggio" in s.lower() and ("emilia" in s.lower() or "nell" in s.lower()):
                return "Reggio Emilia"
            if "reggio" in s.lower() and "calabria" in s.lower():
                return "Reggio Calabria"
            if "forl" in s.lower():
                return "Forlì"
            return s
            
        df_in["comune"] = df_in["comune"].apply(pulisci_nome_comune)
        
        def assegna_fascia_verde(val):
            if pd.isna(val):
                return "Dato non disponibile"
            elif val < 10.0:
                return "0-10% (Critica)"
            elif val < 20.0:
                return "10-20% (Bassa)"
            elif val < 30.0:
                return "20-30% (Media)"
            elif val < 40.0:
                return "30-40% (Elevata)"
            else:
                return "40%+ (Massima)"
                
        df_in["fascia_verde"] = df_in["densita_verde"].apply(assegna_fascia_verde)
        
        def sigla_rischio(val):
            if val == "Alto":
                return "A"
            elif val == "Molto Alto":
                return "M"
            elif val == "Estremo":
                return "E"
            elif val == "Moderato":
                return "Mod"
            return "B"
            
        df_in["sigla_uv"] = df_in["classe_rischio_oms"].apply(sigla_rischio)
        return df_in
    return None

df = load_data()

COLORI_VERDE = {
    "0-10% (Critica)": "#b0bec5",
    "10-20% (Bassa)": "#4caf50",
    "20-30% (Media)": "#00bcd4",
    "30-40% (Elevata)": "#1565c0",
    "40%+ (Massima)": "#6a1b9a",
    "Dato non disponibile": "#757575"
}

COLORI_RISCHIO_OMS = {
    "Basso": "#2e7d32",
    "Moderato": "#fbc02d",
    "Alto": "#fb8c00",
    "Molto Alto": "#c62828",
    "Estremo": "#4a148c"
}

st.sidebar.title("Indice del Progetto")
pagina_selezionata = st.sidebar.radio(
    "Seleziona la sezione:",
    [
        "1. Il Progetto e i Rischi UV",
        "2. Mappa Interattiva Territoriale",
        "3. Grafici e Distribuzioni",
        "4. Conclusioni e Metodologia"
    ]
)

if df is None:
    st.error(f"File dati non trovato: {DATA_PATH}. Eseguire prima il notebook di elaborazione.")
    st.stop()

# ==============================================================================
# PAGINA 1: INTRODUZIONE & QUADRO SCIENTIFICO
# ==============================================================================
if pagina_selezionata == "1. Il Progetto e i Rischi UV":
    st.title("UV-Safe: Radiazione Ultravioletta e Mitigazione Arborea")
    st.markdown("#### Analisi dell'esposizione solare e della copertura di verde urbano nei 110 capoluoghi italiani")
    
    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    st.subheader("Guida alle Misurazioni Adottate")
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("""
        <div class="box-sabbia">
            <h4 style="margin-top:0; color:#4e342e;">Indice UV Massimo (UVI)</h4>
            <b>Che cosa misura:</b> L'Indice UV Globale è l'unità di misura standard internazionale che quantifica l'intensità della radiazione ultravioletta solare efficace nel provocare danni alla cute umana.<br><br>
            <b>Periodo di riferimento:</b> Trimestre estivo compreso tra il <b>1° Giugno e il 31 Agosto 2024</b>.<br><br>
            <b>Fascia oraria critica:</b> Ore <b>11:00 – 16:00</b>, arco di tempo in cui la culminazione solare raggiunge lo zenit determinando i picchi massimi registrati dai sensori.
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown("""
        <div class="box-bosco">
            <h4 style="margin-top:0; color:#1b5e20;">Densità di Verde Urbano (%)</h4>
            <b>Che cosa misura:</b> L'incidenza percentuale della superficie coperta da verde urbano rispetto all'estensione territoriale totale del comune (rilevazione ufficiale ISTAT).<br><br>
            <b>Significato pratico:</b> Non si tratta di un semplice conteggio numerico di piante, ma della <b>quota di suolo cittadino protetta da coperture vegetate</b> (parchi, viali alberati, giardini).<br><br>
            <b>Funzione:</b> Indica quanto spazio urbano beneficia della schermatura delle chiome contro la radiazione diretta al suolo rispetto alle superfici impermeabili e asfaltate.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="box-sabbia">
            <h3 style="margin-top:0; color:#4e342e;">I Pericoli dei Raggi UV</h3>
            I raggi ultravioletti (UV) emessi dal sole sono invisibili ma raggiungono costantemente il suolo.
            <br><br>
            <b>Effetti sulla salute:</b> un'esposizione solare prolungata senza adeguate protezioni provoca scottature ed eritemi nel breve periodo. Nel lungo termine, danneggia le cellule cutanee, accelera l'invecchiamento della pelle e aumenta concretamente il rischio di sviluppare patologie cutanee gravi.
            <br><br>
            <b>Pressione ambientale:</b> nelle aree urbane fortemente edificate l'assenza di coperture naturali amplifica lo stress termico e radiativo per i residenti.
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="box-bosco">
            <h3 style="margin-top:0; color:#1b5e20;">Il Ruolo Protettivo del Verde Urbano</h3>
            I parchi cittadini e i viali alberati rappresentano un presidio naturale fondamentale all'interno delle città.
            <br><br>
            <b>Schermatura naturale:</b> le chiome degli alberi creano una barriera in grado di assorbire e bloccare tra il <b>70% e il 90% della radiazione solare diretta</b> prima che raggiunga marciapiedi e piazze, riducendo drasticamente la quantità di raggi UV assorbiti dai passanti.
            <br><br>
            <b>Aria e vivibilità:</b> oltre a creare corridoi ombreggiati per pedoni e categorie vulnerabili, la vegetazione contribuisce ad attenuare le ondate di calore e a trattenere parte del particolato atmosferico.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)
    
    st.subheader("La Scala Ufficiale dell'Indice UV (WHO / OMS)")
    st.markdown("""
    <div class="box-ardesia">
        L'Organizzazione Mondiale della Sanità (OMS) definisce l'Indice UV (UVI) come parametro internazionale per comunicare il livello di pericolo della radiazione solare e le relative indicazioni di tutela.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <table class="tabella-naturale">
        <thead>
            <tr>
                <th style="width: 15%;">Indice UV</th>
                <th style="width: 20%;">Livello di Rischio</th>
                <th style="width: 65%;">Misure di Tutela Raccomandate</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>0.0 - 2.9</b></td>
                <td><span style="color:#2e7d32; font-weight:bold;">Basso</span></td>
                <td>Nessuna protezione particolare; permanenza all'aperto sicura.</td>
            </tr>
            <tr>
                <td><b>3.0 - 5.9</b></td>
                <td><span style="color:#f57f17; font-weight:bold;">Moderato</span></td>
                <td>Cercare l'ombra nelle ore centrali; consigliati cappello e occhiali da sole.</td>
            </tr>
            <tr>
                <td><b>6.0 - 7.9</b></td>
                <td><span style="color:#e65100; font-weight:bold;">Alto</span></td>
                <td>Protezione indispensabile; muoversi preferibilmente lungo percorsi alberati tra le 11:00 e le 16:00.</td>
            </tr>
            <tr>
                <td><b>8.0 - 10.9</b></td>
                <td><span style="color:#c62828; font-weight:bold;">Molto Alto</span></td>
                <td>Rischio di eritema rapido; evitare l'esposizione diretta e cercare sistematicamente zone d'ombra.</td>
            </tr>
            <tr>
                <td><b>11.0+</b></td>
                <td><span style="color:#4a148c; font-weight:bold;">Estremo</span></td>
                <td>Evitare la permanenza all'aperto nelle ore centrali.</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)
    
    st.subheader("Fonti Ufficiali Utilizzate")
    
    st.markdown("""
    <div class="box-bosco">
        <b>ISTAT — Dati Ambientali nelle Città (Verde Urbano):</b> percentuali ufficiali di superficie coperta da verde nei 110 capoluoghi italiani.<br>
        Collegamento: <a href="https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0920ENV,1.0/ENV_CITIES/DCCV_URBANENV_URBGRE/IT1,609_1_DF_DCCV_URBANENV_18,1.0" target="_blank" style="color:#1b5e20; font-weight:bold;">Catalogo Dati ISTAT DataBrowser</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="box-sabbia">
        <b>Open-Meteo Air Quality & Solar Radiation Archive:</b> registrazioni orarie e massimi giornalieri di radiazione ultravioletta per l'estate 2024.<br>
        Collegamento: <a href="https://open-meteo.com/en/docs/air-quality-api" target="_blank" style="color:#4e342e; font-weight:bold;">Documentazione API Open-Meteo</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="box-ardesia">
        <b>Wikidata Knowledge Base:</b> arricchimento geografico e semantico a 5 stelle mediante codici ISTAT univoci e coordinate WGS84 certificate.<br>
        Collegamento: <a href="https://query.wikidata.org/" target="_blank" style="color:#37474f; font-weight:bold;">Wikidata SPARQL Query Service</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="box-bosco">
        <b>World Health Organization (WHO / OMS):</b> linee guida sanitarie internazionali sull'Indice UV.<br>
        Collegamento: <a href="https://www.who.int/publications/i/item/9241590076" target="_blank" style="color:#1b5e20; font-weight:bold;">Guida Ufficiale WHO Global Solar UV Index</a>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# PAGINA 2: ANALISI TERRITORIALE & MAPPA
# ==============================================================================
elif pagina_selezionata == "2. Mappa Interattiva Territoriale":
    st.title("Mappa Interattiva dei 110 Capoluoghi Italiani")
    
    st.markdown("""
    <div class="box-sabbia">
        La cartografia confronta visivamente la disponibilità di aree verdi e la severità dei picchi di radiazione solare:
        <br>
        • <b>Il colore del marcatore</b> rappresenta la <b>densità di verde urbano</b> (classificata su 5 fasce percentuali).<br>
        • <b>La lettera all'interno del cerchio</b> indica la classe di rischio UV OMS: <b>M</b> per Rischio <i>Molto Alto</i> (UVI 8.0 - 10.9) e <b>A</b> per Rischio <i>Alto</i> (UVI 6.0 - 7.9).
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    st.sidebar.subheader("Filtri Territoriali")
    fasce_scelte = st.sidebar.multiselect(
        "Filtra per Fascia di Verde:",
        options=list(COLORI_VERDE.keys())[:-1],
        default=list(COLORI_VERDE.keys())[:-1]
    )
    
    rischi_scelti = st.sidebar.multiselect(
        "Filtra per Livello UV:",
        options=["Alto", "Molto Alto"],
        default=["Alto", "Molto Alto"]
    )

    df_map = df[(df["fascia_verde"].isin(fasce_scelte)) & (df["classe_rischio_oms"].isin(rischi_scelti))]

    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Capoluoghi Visualizzati", f"{len(df_map)} su {len(df)}")
    col_k2.metric("UV Max Medio Estivo", f"{df_map['uv_max'].mean():.2f}")
    col_k3.metric("Densità Media Verde", f"{df_map['densita_verde'].mean():.2f}%")

    st.markdown("""
    <div style="margin-bottom: 15px; margin-top: 15px;">
        <b>Legenda Densità Verde Urbano:</b>
        <span style='background-color:#b0bec5; padding:3px 10px; border-radius:4px; color:#000; font-weight:bold;'>0-10% Critico</span> &nbsp;
        <span style='background-color:#4caf50; padding:3px 10px; border-radius:4px; color:#fff; font-weight:bold;'>10-20% Basso</span> &nbsp;
        <span style='background-color:#00bcd4; padding:3px 10px; border-radius:4px; color:#fff; font-weight:bold;'>20-30% Medio</span> &nbsp;
        <span style='background-color:#1565c0; padding:3px 10px; border-radius:4px; color:#fff; font-weight:bold;'>30-40% Elevato</span> &nbsp;
        <span style='background-color:#6a1b9a; padding:3px 10px; border-radius:4px; color:#fff; font-weight:bold;'>40%+ Massimo</span>
        <br><br>
        <b>Lettera nel cerchio:</b> <b>M</b> = UV Molto Alto (8.0 - 10.9) | <b>A</b> = UV Alto (6.0 - 7.9)
    </div>
    """, unsafe_allow_html=True)

    tile_esri = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
    attr_esri = "Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS User Community"
    
    m = folium.Map(location=[42.1, 12.8], zoom_start=6, tiles=tile_esri, attr=attr_esri)

    for _, row in df_map.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        comune = row["comune"]
        
        # Gestione pulita dei valori nulli per evitare 'nan' o 'nan%' a video
        uv_str = f"{row['uv_max']:.2f}" if pd.notna(row['uv_max']) else "Dato non rilevato"
        verde_str = f"{row['densita_verde']:.1f}%" if pd.notna(row['densita_verde']) else "Dato non disponibile"
        rischio = row["classe_rischio_oms"] if pd.notna(row["classe_rischio_oms"]) else "Non classificato"
        fascia_v = row["fascia_verde"]
        sigla = row["sigla_uv"]
        wiki_url = row["wikidata_uri"] if (pd.notna(row["wikidata_uri"]) and str(row["wikidata_uri"]).startswith("http")) else "#"
        colore_punto = COLORI_VERDE.get(fascia_v, "#757575")

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 190px; font-size: 13px;">
            <h4 style="margin: 0 0 6px 0; color: #1b5e20;">{comune}</h4>
            <b>Codice ISTAT:</b> {row['istat_code']}<br>
            <b>Picco UV Estivo:</b> {uv_str} ({rischio})<br>
            <b>Densità Verde:</b> {verde_str} ({fascia_v})<br>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #ddd;">
            <a href="{wiki_url}" target="_blank" style="color: #1b5e20; font-weight: bold; text-decoration: none;">Visualizza scheda su Wikidata</a>
        </div>
        """

        icon_html = f"""
        <div style="
            background-color: {colore_punto};
            width: 26px;
            height: 26px;
            border-radius: 50%;
            border: 2px solid #ffffff;
            box-shadow: 0 0 4px rgba(0,0,0,0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            font-weight: bold;
            font-family: Arial, sans-serif;">
            {sigla}
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=icon_html, icon_size=(26, 26), icon_anchor=(13, 13)),
            popup=folium.Popup(popup_html, max_width=280)
        ).add_to(m)

    st_folium(m, width=1150, height=600)

# ==============================================================================
# PAGINA 3: ANALISI GRAFICA
# ==============================================================================
elif pagina_selezionata == "3. Grafici e Distribuzioni":
    st.title("Distribuzioni e Confronti Statistici")
    
    st.markdown("""
    <div class="box-ardesia">
        Questa sezione analizza quantitativamente i dati: a sinistra la classificazione della radiazione UV, a destra la disponibilità di aree verdi e in basso l'incrocio tra le due grandezze per ciascuna città.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Livelli di Pericolo UV (OMS)")
        fig1, ax1 = plt.subplots(figsize=(6, 4.5))
        ord_rischio = ["Alto", "Molto Alto"]
        presenti_rischio = [r for r in ord_rischio if r in df["classe_rischio_oms"].values]
        palette_uv = [COLORI_RISCHIO_OMS[r] for r in presenti_rischio]

        sns.countplot(
            data=df,
            x="classe_rischio_oms",
            order=presenti_rischio,
            palette=palette_uv,
            ax=ax1
        )
        ax1.set_xlabel("Classe OMS", fontsize=10)
        ax1.set_ylabel("Numero di Comuni", fontsize=10)
        ax1.grid(axis='y', linestyle='--', alpha=0.4)
        st.pyplot(fig1)
        st.caption("Frequenza dei comuni: 101 su 110 si collocano nella classe 'Molto Alto' (rosso).")

    with col_g2:
        st.subheader("Fasce di Densità del Verde Urbano")
        fig2, ax2 = plt.subplots(figsize=(6, 4.5))
        ord_fasce = ["0-10% (Critica)", "10-20% (Bassa)", "20-30% (Media)", "30-40% (Elevata)", "40%+ (Massima)"]
        presenti_verde = [f for f in ord_fasce if f in df["fascia_verde"].values]
        palette_v = [COLORI_VERDE[f] for f in presenti_verde]

        sns.countplot(
            data=df,
            x="fascia_verde",
            order=presenti_verde,
            palette=palette_v,
            ax=ax2
        )
        ax2.set_xlabel("Fascia di Densità del Verde (%)", fontsize=10)
        ax2.set_ylabel("Numero di Comuni", fontsize=10)
        ax2.grid(axis='y', linestyle='--', alpha=0.4)
        plt.xticks(rotation=20)
        st.pyplot(fig2)
        st.caption("Distribuzione dei capoluoghi: la maggioranza si colloca nella fascia inferiore al 10%.")

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)
    
    st.subheader("Dispersione: Densità di Verde vs Picco UV")
    
    st.markdown("""
    <div class="box-bosco">
        Il grafico seguente posiziona i 110 capoluoghi italiani:
        <br>
        • <b>Asse orizzontale (X):</b> percentuale di verde urbano rispetto al territorio comunale.<br>
        • <b>Asse verticale (Y):</b> picco massimo di indice UV registrato durante l'estate 2024.<br>
        Seleziona un comune dal menu in basso: il corrispondente <b>pallino cambierà colore evidenziandosi in oro brillante</b> con un puntatore dedicato sul grafico.
    </div>
    """, unsafe_allow_html=True)

    elenco_citta = sorted(df["comune"].unique())
    idx_default = elenco_citta.index("Torino") if "Torino" in elenco_citta else 0
    
    citta_scelta = st.selectbox(
        "Seleziona un comune da evidenziare nel grafico sottostante:",
        options=elenco_citta,
        index=idx_default
    )
    
    row_sel = df[df["comune"] == citta_scelta].iloc[0]
    x_sel = float(row_sel["densita_verde"]) if pd.notna(row_sel["densita_verde"]) else 0.0
    y_sel = float(row_sel["uv_max"]) if pd.notna(row_sel["uv_max"]) else 0.0

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    sns.scatterplot(
        data=df,
        x="densita_verde",
        y="uv_max",
        hue="classe_rischio_oms",
        palette=COLORI_RISCHIO_OMS,
        s=80,
        alpha=0.6,
        edgecolor="#555555",
        linewidth=0.5,
        ax=ax3
    )
    
    ax3.scatter(
        [x_sel], [y_sel],
        color="#ffd600",
        s=260,
        edgecolor="#d50000",
        linewidth=2.5,
        zorder=10,
        label=f"Selezionato: {citta_scelta}"
    )
    
    ax3.annotate(
        f"{citta_scelta} ({x_sel:.1f}%, UVI {y_sel:.2f})",
        xy=(x_sel, y_sel),
        xytext=(x_sel + 2.5, y_sel + 0.15),
        arrowprops=dict(facecolor="#d50000", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10,
        fontweight='bold',
        color="#b71c1c",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fff9c4", ec="#d50000", lw=1.2)
    )

    ax3.set_xlabel("Densità Verde Urbano (%)", fontsize=11)
    ax3.set_ylabel("Picco UV Estivo 2024", fontsize=11)
    ax3.grid(True, linestyle='--', alpha=0.4)
    ax3.legend(title="Legenda e Comune", loc="upper right")
    st.pyplot(fig3)

    st.markdown(f"""
    <div class="box-sabbia">
        <b>Dettaglio Comune Selezionato: {row_sel['comune']}</b> (Codice ISTAT: {row_sel['istat_code']})<br>
        • <b>Picco UV Estivo:</b> {y_sel:.2f} (Classe OMS: <b>{row_sel['classe_rischio_oms']}</b>)<br>
        • <b>Densità di Verde Urbano:</b> {x_sel:.1f}% (Fascia: <b>{row_sel['fascia_verde']}</b>)<br>
        • <b>Posizione sul piano cartesiano:</b> Asse X (Verde) = <b>{x_sel:.1f}%</b>, Asse Y (UVI Max) = <b>{y_sel:.2f}</b>.
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# PAGINA 4: CONCLUSIONI & METODOLOGIA
# ==============================================================================
elif pagina_selezionata == "4. Conclusioni e Metodologia":
    st.title("Conclusioni e Documentazione della Pipeline Dati")
    
    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    tot_comuni = len(df)
    molto_alto = df[df["classe_rischio_oms"] == "Molto Alto"]
    tot_molto_alto = len(molto_alto)
    
    sotto_10 = len(molto_alto[molto_alto["densita_verde"] < 10.0])
    pct_sotto_10 = (sotto_10 / tot_molto_alto) * 100 if tot_molto_alto > 0 else 0
    
    tra_10_20 = len(molto_alto[(molto_alto["densita_verde"] >= 10.0) & (molto_alto["densita_verde"] < 20.0)])
    pct_tra_10_20 = (tra_10_20 / tot_molto_alto) * 100 if tot_molto_alto > 0 else 0
    
    sopra_20 = len(molto_alto[molto_alto["densita_verde"] >= 20.0])
    pct_sopra_20 = (sopra_20 / tot_molto_alto) * 100 if tot_molto_alto > 0 else 0

    st.markdown(f"""
    <div class="box-sabbia">
        <h3 style="margin-top:0; color:#4e342e;">Evidenze Territoriali: Dove si Collocano i Capoluoghi</h3>
        L'incrocio tra le serie radiometriche e le rilevazioni ISTAT sul verde evidenzia un quadro territoriale chiaro:
        <br><br>
        • <b>Pressione solare omogenea:</b> su <b>{tot_comuni} capoluoghi</b>, ben <b>{tot_molto_alto} città</b> raggiungono la classe di allerta <b>Molto Alto (UVI compreso tra 8.0 e 10.9)</b> durante l'estate 2024. Questo dimostra come l'esigenza di percorsi protetti e zone d'ombra sia comune a tutte le latitudini italiane.<br><br>
        • <b>Comuni in fascia critica (&lt; 10% di verde):</b> tra le città con rischio UV Molto Alto, il <b>{pct_sotto_10:.1f}% ({sotto_10} comuni)</b> dispone di una percentuale di verde inferiore al 10%. In queste realtà la protezione naturale fornita dalle chiome arboree è particolarmente ridotta.<br><br>
        • <b>Comuni in fascia intermedia (10% - 20%):</b> il <b>{pct_tra_10_20:.1f}% ({tra_10_20} comuni)</b> presenta una dotazione intermedia di aree verdi.<br><br>
        • <b>Comuni ad elevata mitigazione (&ge; 20%):</b> soltanto il <b>{pct_sopra_20:.1f}% ({sopra_20} comuni)</b> supera la quota del 20% di superficie verde, offrendo una presenza più diffusa di parchi e viali alberati per ripararsi nelle ore centrali della giornata.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    st.subheader("La Pipeline di Elaborazione dei Dati")
    
    st.markdown("""
    <div class="box-bosco">
        <b>1. Acquisizione e Pulizia (Livello 3 Stelle):</b> integrazione del dataset ISTAT sul verde urbano e delle rilevazioni orarie UV di Open-Meteo; normalizzazione dei codici ISTAT ufficiali a 6 cifre e rimozione delle aggregazioni territoriali non comunali.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-ardesia">
        <b>2. Riconciliazione e Interlinking con Wikidata (Livello 5 Stelle):</b> esecuzione di query SPARQL per connettere ciascun comune al proprio identificatore canonico in Wikidata, associando le coordinate geografiche certificate con una copertura pari al 100%.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-sabbia">
        <b>3. Classificazione Sanitaria Standardizzata:</b> conversione dei valori fisici UVI nelle classi di allerta definite dalle linee guida congiunte di OMS ed EPA.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-bosco">
        <b>4. Modellazione Semantica e Grafo RDF:</b> formalizzazione del dominio mediante ontologia OWL e serializzazione delle istanze nel Knowledge Graph standard Turtle, salvato nel file output/uv_safe_graph.ttl con prefissi standard e URI stabili.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divisore-naturale"></div>', unsafe_allow_html=True)

    st.subheader("Disponibilità del Dataset Elaborato")
    st.dataframe(df, use_container_width=True)
    
    csv_out = df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        label="Scarica Dataset Consolidato (CSV 3 Stelle)",
        data=csv_out,
        file_name="uv_safe_capoluoghi_2024.csv",
        mime="text/csv"
    )