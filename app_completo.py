import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

st.set_page_config(page_title="Procesador de Horas", page_icon="🕒")

st.title("🕒 Procesador de Horas Trabajadas")
st.markdown("""
Sube tu archivo **Formato_Carga(C).xlsx** para calcular automáticamente horas normales, extras, nocturnas y más.
""")

def convertir_a_str(hora):
    if isinstance(hora, time):
        return hora.strftime("%H:%M:%S")
    elif isinstance(hora, str):
        return hora
    return None

def calcular_horas_extra_reales(inicio_raw, fin_raw, refrigerio_inicio_raw=None, refrigerio_fin_raw=None):
    try:
        formato = "%H:%M:%S"
        inicio = datetime.strptime(convertir_a_str(inicio_raw), formato)
        fin = datetime.strptime(convertir_a_str(fin_raw), formato)
        if fin <= inicio:
            fin += timedelta(days=1)

        descuento_refrigerio_min = 0
        if refrigerio_inicio_raw and refrigerio_fin_raw:
            ri = datetime.strptime(convertir_a_str(refrigerio_inicio_raw), formato).time()
            rf = datetime.strptime(convertir_a_str(refrigerio_fin_raw), formato).time()
            if ri == time(13, 0) and rf == time(14, 0):
                descuento_refrigerio_min = 60
            elif ri == time(12, 0) and rf == time(12, 45):
                descuento_refrigerio_min = 45

        total_min = int((fin - inicio).total_seconds() / 60) - descuento_refrigerio_min
        minutos_normales = min(total_min, 480)
        minutos_extras = max(total_min - 480, 0)
        inicio_extras_real = inicio + timedelta(minutes=480 + descuento_refrigerio_min)

        extra_25_d = extra_25_n = extra_35_d = extra_35_n = 0
        for i in range(minutos_extras):
            momento = inicio_extras_real + timedelta(minutes=i)
            hora = momento.time()
            es_nocturna = hora >= time(22, 0) or hora < time(6, 0)

            if i < 120:
                if es_nocturna:
                    extra_25_n += 1
                else:
                    extra_25_d += 1
            else:
                if es_nocturna:
                    extra_35_n += 1
                else:
                    extra_35_d += 1

        return [
            round(minutos_normales / 60, 2),
            round(extra_25_d / 60, 2),
            round(extra_25_n / 60, 2),
            round(extra_35_d / 60, 2),
            round(extra_35_n / 60, 2)
        ]

    except Exception:
        return [0, 0, 0, 0, 0]

def procesar_dataframe(df):
    def procesar_fila(row):
        resultado = calcular_horas_extra_reales(
            row["Hora Inicio Labores"],
            row["Hora Término Labores"],
            row.get("Hora Inicio Refrigerio", None),
            row.get("Hora Término Refrigerio", None)
        )
        return pd.Series({
            "Horas Normales": resultado[0],
            "Extra 25%": resultado[1],
            "Extra 25% Nocturna": resultado[2],
            "Extra 35%": resultado[3],
            "Extra 35% Nocturna": resultado[4],
        })

    resultados = df.apply(procesar_fila, axis=1)
    return pd.concat([df, resultados], axis=1)

archivo = st.file_uploader("📁 Selecciona el archivo Excel", type=["xlsx"])

if archivo:
    if "Formato_Carga" not in archivo.name:
        st.warning("⚠️ Se recomienda que el archivo se llame 'Formato_Carga(C).xlsx' para evitar confusión.")

    try:
        df = pd.read_excel(archivo, sheet_name="Horas")
        st.success("✅ Archivo cargado correctamente.")
        st.markdown("### Vista previa de datos:")
        st.dataframe(df.head())

        resultado = procesar_dataframe(df)
        st.markdown("### ✅ Resultado procesado:")
        st.dataframe(resultado)

        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            resultado.to_excel(writer, index=False)
        st.download_button("⬇️ Descargar reporte", data=output.getvalue(),
                           file_name="reporte_horas_final(C).xlsx")

    except Exception as e:
        st.error(f"❌ Error procesando archivo: {e}")
