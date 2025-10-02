from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte de Limpieza Semanal', 0, 1, 'C')
        self.ln(5)
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, body)
        self.ln()

def generate_pdf_report(records, week_dates):
    """Genera un reporte PDF del historial de limpieza"""
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        # Información de la semana
        pdf.chapter_title(f'Semana del {week_dates[0].strftime("%d/%m/%Y")} al {week_dates[-1].strftime("%d/%m/%Y")}')
        pdf.chapter_body(f'Reporte generado el: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        pdf.ln(10)
        
        # Resumen por días
        for day_date in week_dates:
            day_name = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][day_date.weekday()]
            day_records = [r for r in records if datetime.strptime(r['fecha'], '%Y-%m-%d').date() == day_date]
            
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f'{day_name} - {day_date.strftime("%d/%m/%Y")}', 0, 1)
            
            if day_records:
                pdf.set_font('Arial', '', 10)
                for record in day_records:
                    estudiantes = ', '.join(record['estudiantes'])
                    pdf.multi_cell(0, 6, f'• {record["tipo_limpieza"]}: {estudiantes} - {record["hora"]}')
            else:
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 6, '  No hay registros de limpieza', 0, 1)
            
            pdf.ln(2)
        
        # Estadísticas
        pdf.ln(10)
        pdf.chapter_title('Estadísticas de la Semana')
        
        total_limpiezas = len(records)
        aula_count = len([r for r in records if r['tipo_limpieza'] == 'Aula'])
        banos_count = len([r for r in records if r['tipo_limpieza'] == 'Baños'])
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f'Total de limpiezas registradas: {total_limpiezas}', 0, 1)
        pdf.cell(0, 8, f'Limpiezas de aula: {aula_count}', 0, 1)
        pdf.cell(0, 8, f'Limpiezas de baños: {banos_count}', 0, 1)
        
        # Guardar PDF
        filename = f"reporte_limpieza_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename)
        
        return filename
    except Exception as e:
        raise Exception(f"Error al generar PDF: {e}")

# Esto asegura que la función esté disponible cuando se importe el módulo
__all__ = ['generate_pdf_report']