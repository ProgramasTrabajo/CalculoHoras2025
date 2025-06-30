import pandas as pd
from datetime import datetime, timedelta, time

class WorkHoursCalculator:
    """
    A class to handle complex work hours calculations including regular hours,
    overtime at different rates, and special cases for weekends and holidays.
    """
    
    def __init__(self):
        self.formato_hora = "%H:%M:%S"
        self.dias_normales = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado']
    
    def convertir_a_str(self, hora):
        """Convert time object to string format"""
        if isinstance(hora, time):
            return hora.strftime(self.formato_hora)
        elif isinstance(hora, str):
            return hora
        return None
    
    def calcular_horas(self, inicio_raw, fin_raw, refrigerio_inicio_raw=None, refrigerio_fin_raw=None):
        """
        Calculate work hours with complex overtime and shift logic
        
        Returns:
            tuple: (horas_diurnas, horas_nocturnas, horas_normales, extra_25, 
                   extra_35, extra_25_nocturna, extra_35_nocturna, total_horas)
        """
        inicio_str = self.convertir_a_str(inicio_raw)
        fin_str = self.convertir_a_str(fin_raw)
        refrigerio_inicio_str = self.convertir_a_str(refrigerio_inicio_raw)
        refrigerio_fin_str = self.convertir_a_str(refrigerio_fin_raw)

        if not inicio_str or not fin_str:
            return [0]*8

        try:
            inicio = datetime.strptime(inicio_str, self.formato_hora)
            fin = datetime.strptime(fin_str, self.formato_hora)
            
            # Handle overnight shifts
            if fin <= inicio:
                fin += timedelta(days=1)

            # Calculate break time
            minutos_refrigerio = 0
            if refrigerio_inicio_str and refrigerio_fin_str:
                ri = datetime.strptime(refrigerio_inicio_str, self.formato_hora).time()
                rf = datetime.strptime(refrigerio_fin_str, self.formato_hora).time()
                if ri == time(13, 0) and rf == time(14, 0):
                    minutos_refrigerio = 60
                elif ri == time(12, 0) and rf == time(12, 45):
                    minutos_refrigerio = 45

            # Calculate daytime and nighttime minutes
            minutos_diurnos_total = 0
            minutos_nocturnos_total = 0

            actual = inicio
            while actual < fin:
                hora = actual.time()
                if time(6, 0) <= hora < time(22, 0):  # 6 AM to 10 PM is daytime
                    minutos_diurnos_total += 1
                else:
                    minutos_nocturnos_total += 1
                actual += timedelta(minutes=1)

            total_minutos = minutos_diurnos_total + minutos_nocturnos_total

            # Subtract break time
            if minutos_refrigerio > 0:
                if minutos_diurnos_total >= minutos_refrigerio:
                    minutos_diurnos_total -= minutos_refrigerio
                else:
                    restante = minutos_refrigerio - minutos_diurnos_total
                    minutos_diurnos_total = 0
                    minutos_nocturnos_total = max(0, minutos_nocturnos_total - restante)
                total_minutos -= minutos_refrigerio

            # Calculate regular vs overtime minutes
            minutos_normales = min(total_minutos, 480)  # 8 hours = 480 minutes
            minutos_extras = max(0, total_minutos - 480)

            # Calculate normal daytime and nighttime hours
            minutos_diurnos_normales = 0
            minutos_nocturnos_normales = 0
            actual = inicio
            minutos_asignados = 0
            
            while actual < fin and minutos_asignados < minutos_normales:
                hora = actual.time()
                if time(6, 0) <= hora < time(22, 0):
                    minutos_diurnos_normales += 1
                else:
                    minutos_nocturnos_normales += 1
                minutos_asignados += 1
                actual += timedelta(minutes=1)

            # Convert to hours
            horas_diurnas = minutos_diurnos_normales / 60
            horas_nocturnas = minutos_nocturnos_normales / 60

            # Calculate overtime rates
            horas_extra_25 = min(minutos_extras, 120) / 60  # First 2 hours at 25%
            horas_extra_35 = max(minutos_extras - 120, 0) / 60  # Beyond 2 hours at 35%

            # Initialize nighttime overtime
            horas_extra_25_nocturna = 0
            horas_extra_35_nocturna = 0

            # Special cases for afternoon/evening shifts
            if inicio.time() >= time(15, 0) and inicio.time() < time(20, 0):
                horas_extra_25_nocturna = horas_extra_25
                horas_extra_35_nocturna = round(horas_diurnas, 2) - horas_extra_25_nocturna
                horas_extra_25 = 0
                horas_extra_35 = horas_extra_35 - horas_extra_35_nocturna

            if inicio.time() >= time(20, 0) and inicio.time() < time(22, 0):
                horas_extra_25_nocturna = round(horas_diurnas, 2)
                horas_extra_35_nocturna = 0
                horas_extra_25 = horas_extra_25 - horas_extra_25_nocturna

            # Handle late night endings
            if fin.time() >= time(22, 0):
                horas_extra_35_nocturna = ((fin - datetime.combine(fin.date(), time(22, 0))).seconds / 60) / 60
                horas_extra_35 = horas_extra_35 - horas_extra_35_nocturna

            # Handle early morning endings (overnight shifts)
            if fin.time() < time(6, 0):
                inicio_nocturno = datetime.combine(fin.date(), time(22, 0)) - timedelta(days=1)
                diferencia = fin - inicio_nocturno
                horas_extra_35_nocturna = (diferencia.seconds / 60) / 60
                horas_extra_35 = horas_extra_35 - horas_extra_35_nocturna

            total_horas = (minutos_diurnos_total + minutos_nocturnos_total) / 60

            # Return all values, ensuring no negative numbers
            return (
                max(round(horas_diurnas, 2), 0),
                max(round(horas_nocturnas, 2), 0),
                max(round(minutos_normales / 60, 2), 0),
                max(round(horas_extra_25, 2), 0),
                max(round(horas_extra_35, 2), 0),
                max(round(horas_extra_25_nocturna, 2), 0),
                max(round(horas_extra_35_nocturna, 2), 0),
                max(round(total_horas, 2), 0)
            )

        except Exception as e:
            print(f"Error calculating hours: {e}")
            return [0]*8

    def procesar_fila(self, row):
        """Process a single row of work hours data"""
        resultado = self.calcular_horas(
            row["Hora Inicio Labores"],
            row["Hora Término Labores"],
            row.get("Hora Inicio Refrigerio", None),
            row.get("Hora Término Refrigerio", None)
        )

        dia = str(row["DIA"]).strip().lower()

        if dia in self.dias_normales:
            # Regular weekdays and Saturdays
            return pd.Series({
                "Horas Diurnas": resultado[0],
                "Extra 25%": resultado[3],
                "Extra 35%": resultado[4],
                "Horas Nocturnas": resultado[1],
                "Extra 25% Nocturna": resultado[5],
                "Extra 35% Nocturna": resultado[6],
                "Horas Domingo/Feriado": 0,
                "Horas Extra Domingo/Feriado": 0,
                "Horas Normales": resultado[2],
                "Total Horas": resultado[7],
            })
        else:
            # Sundays and holidays
            total_horas = resultado[7]
            base = min(total_horas, 8)
            extra = max(total_horas - 8, 0)
            return pd.Series({
                "Horas Diurnas": 0,
                "Extra 25%": 0,
                "Extra 35%": 0,
                "Horas Nocturnas": 0,
                "Extra 25% Nocturna": 0,
                "Extra 35% Nocturna": 0,
                "Horas Domingo/Feriado": round(base, 2),
                "Horas Extra Domingo/Feriado": round(extra, 2),
                "Horas Normales": 0,
                "Total Horas": total_horas,
            })

    def calcular_dia_tra(self, row):
        """Calculate DIA-TRA value (workday indicator)"""
        dia = row["DIA"].strip().lower()
        es_laboral = dia in self.dias_normales
        tiene_horas = row["Horas Diurnas"] + row["Horas Nocturnas"] > 0
        
        # Special case for medical leave
        if row["Labor/Actividad"] == "Descanso Médico":
            return "DM"
        
        return 1 if es_laboral and tiene_horas else 0

    def process_dataframe(self, df):
        """
        Process the entire dataframe with work hours calculations
        
        Args:
            df (pandas.DataFrame): Input dataframe with work hours data
            
        Returns:
            pandas.DataFrame: Processed dataframe with calculated hours
        """
        # Store original columns
        columnas_ingreso = df.columns.tolist()
        
        # Apply hour calculations to each row
        resultados = df.apply(self.procesar_fila, axis=1, result_type="expand")
        
        # Combine original data with results
        df_resultado = pd.concat([df, resultados], axis=1)
        
        # Calculate DIA-TRA column
        df_resultado["DIA-TRA"] = df_resultado.apply(self.calcular_dia_tra, axis=1)
        
        # Define final column order
        columnas_orden = [
            "Horas Diurnas", "Extra 25%", "Extra 35%", "Horas Nocturnas",
            "Extra 25% Nocturna", "Extra 35% Nocturna",
            "Horas Domingo/Feriado", "Horas Extra Domingo/Feriado",
            "Horas Normales", "Total Horas"
        ]
        
        # Reorder columns: original + DIA-TRA + calculated columns
        df_resultado = df_resultado[columnas_ingreso + ["DIA-TRA"] + columnas_orden]
        
        return df_resultado
