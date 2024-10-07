import streamlit as st
import pandas as pd
from datetime import datetime

# Cargar los datos desde un archivo o una base de datos
@st.cache
def load_data():
    # Aquí se cargarían los datos desde la base de datos o archivo Excel
    df = pd.read_excel("CONTROL DE GESTION DE LA DGEI- 2024 -300924_FINAL.xlsx", sheet_name="ENTRADA CORRESPONDENCIA DGEI")
    df["FECHA DE VENCIMIENTO"] = pd.to_datetime(df["FECHA DE VENCIMIENTO"], errors='coerce')
    df["DIAS DISPONIBLES PARA ATENCIÓN"] = (df["FECHA DE VENCIMIENTO"] - pd.to_datetime(datetime.now())).dt.days
    return df

df = load_data()

# Título de la aplicación
st.title("Monitoreo de Correspondencia DGEI")

# Filtro de búsqueda por número de oficio o remitente
search_term = st.text_input("Buscar por número de oficio o remitente", "")

if search_term:
    df = df[df["N° DE OFICIO"].str.contains(search_term, na=False, case=False) | 
            df["REMITENTE"].str.contains(search_term, na=False, case=False)]

# Opción para ordenar por proximidad a la fecha de vencimiento
sort_by_vencimiento = st.checkbox("Ordenar por proximidad a caducar")

if sort_by_vencimiento:
    df = df.sort_values("DIAS DISPONIBLES PARA ATENCIÓN", ascending=True)

# Mostrar tabla con formato de colores según los días restantes
st.subheader("Lista de Oficios")

def row_style(row):
    days_left = row["DIAS DISPONIBLES PARA ATENCIÓN"]
    if pd.isnull(days_left):
        return [""] * len(row)
    if days_left > 3:
        return ['background-color: lightgreen'] * len(row)
    elif 1 <= days_left <= 2:
        return ['background-color: yellow'] * len(row)
    elif days_left < 1:
        return ['background-color: red'] * len(row)
    return [""] * len(row)

# Agregar columna para marcar como finalizado
df["Marcar Finalizado"] = False

def marcar_finalizado(index):
    df.loc[index, "ESTATUS"] = "CONCLUIDO"

# Mostrar la tabla con colores
styled_df = df.style.apply(row_style, axis=1)

st.dataframe(styled_df)

# Permitir marcar oficios como finalizados
for index, row in df.iterrows():
    if st.button(f"Marcar como finalizado", key=index):
        marcar_finalizado(index)

# Guardar los cambios en la base de datos si se marcó algún oficio como finalizado
# Aquí se implementaría la lógica de guardado en Deta.sh o en el archivo.