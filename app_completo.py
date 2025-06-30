import streamlit as st
import pandas as pd
import io
from datetime import datetime
from work_hours_calculator import WorkHoursCalculator

@st.cache_data
def convert_df_to_excel(df):
    """Convert DataFrame to Excel format for download"""
    # Create a temporary filename
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        df.to_excel(tmp_file.name, index=False, engine='xlsxwriter', sheet_name='Horas Procesadas')
        tmp_file.seek(0)
        
        # Read the file content
        with open(tmp_file.name, 'rb') as f:
            data = f.read()
        
        # Clean up the temporary file
        os.unlink(tmp_file.name)
        
    return data

def main():
    st.set_page_config(
        page_title="Calculadora de Horas de Trabajo",
        page_icon="⏰",
        layout="wide"
    )
    
    st.title("⏰ Calculadora de Horas de Trabajo")
    st.markdown("Sube un archivo Excel para calcular horas de trabajo con horas extras y diferenciales de turno")
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 Instrucciones")
        st.markdown("""
        1. **Subir Archivo Excel**: Selecciona tu archivo Excel de horas de trabajo
        2. **Columnas Requeridas**:
           - DIA (Día de la semana)
           - Hora Inicio Labores (Hora de inicio)
           - Hora Término Labores (Hora de término)
           - Labor/Actividad (Actividad laboral)
        3. **Columnas Opcionales**:
           - Hora Inicio Refrigerio (Inicio de refrigerio)
           - Hora Término Refrigerio (Fin de refrigerio)
        4. **Descargar**: Obtén tu archivo Excel procesado
        """)
        
        st.header("📊 Tipos de Cálculo")
        st.markdown("""
        - **Horas Regulares**: Diurnas/Nocturnas
        - **Horas Extras**: Tarifas del 25% y 35%
        - **Horas Fin de Semana/Feriados**
        - **Licencia Médica**: Manejo especial
        """)
    
    # File upload section
    st.header("📁 Subir Archivo")
    uploaded_file = st.file_uploader(
        "Selecciona un archivo Excel",
        type=['xlsx', 'xls'],
        help="Sube tu archivo Excel de horas de trabajo para procesarlo"
    )
    
    if uploaded_file is not None:
        try:
            # Display file info
            st.success(f"✅ Archivo subido: {uploaded_file.name}")
            
            # Read the Excel file
            with st.spinner("Leyendo archivo Excel..."):
                df = pd.read_excel(uploaded_file)
            
            st.info(f"📊 Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
            
            # Display original data preview
            st.subheader("📋 Vista Previa de Datos Originales")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Validate required columns
            calculator = WorkHoursCalculator()
            required_columns = ['DIA', 'Hora Inicio Labores', 'Hora Término Labores', 'Labor/Actividad']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Faltan columnas requeridas: {', '.join(missing_columns)}")
                st.stop()
            
            # Process the data
            if st.button("🚀 Procesar Horas de Trabajo", type="primary"):
                with st.spinner("Procesando horas de trabajo... Esto puede tomar un momento."):
                    try:
                        processed_df = calculator.process_dataframe(df)
                        
                        st.success("✅ ¡Procesamiento completado exitosamente!")
                        
                        # Display results
                        st.subheader("📊 Resultados Procesados")
                        st.dataframe(processed_df, use_container_width=True)
                        
                        # Summary statistics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_regular = processed_df['Horas Normales'].sum()
                            st.metric("Total Horas Regulares", f"{total_regular:.2f}")
                        
                        with col2:
                            total_overtime = processed_df[['Extra 25%', 'Extra 35%']].sum().sum()
                            st.metric("Total Horas Extras", f"{total_overtime:.2f}")
                        
                        with col3:
                            total_weekend = processed_df[['Horas Domingo/Feriado', 'Horas Extra Domingo/Feriado']].sum().sum()
                            st.metric("Total Horas Fines de Semana/Feriados", f"{total_weekend:.2f}")
                        
                        with col4:
                            total_hours = processed_df['Total Horas'].sum()
                            st.metric("Total General de Horas", f"{total_hours:.2f}")
                        
                        # Download section
                        st.subheader("📥 Descargar Resultados")
                        
                        # Prepare download
                        excel_data = convert_df_to_excel(processed_df)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"horas_trabajo_procesadas_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 Descargar Archivo Excel Procesado",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error procesando datos: {str(e)}")
                        st.exception(e)
        
        except Exception as e:
            st.error(f"❌ Error leyendo archivo: {str(e)}")
            st.exception(e)
    
    else:
        st.info("👆 Por favor sube un archivo Excel para comenzar")
        
        # Show sample data format
        st.subheader("📋 Formato Excel Esperado")
        sample_data = {
            'DIA': ['Lunes', 'Martes', 'Domingo'],
            'Hora Inicio Labores': ['08:00:00', '14:00:00', '09:00:00'],
            'Hora Término Labores': ['17:00:00', '23:00:00', '18:00:00'],
            'Labor/Actividad': ['Regular', 'Regular', 'Trabajo Feriado'],
            'Hora Inicio Refrigerio': ['13:00:00', '', ''],
            'Hora Término Refrigerio': ['14:00:00', '', '']
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)

if __name__ == "__main__":
    main()
