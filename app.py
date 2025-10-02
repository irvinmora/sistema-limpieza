import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import os
import base64

# SOLUCIÓN: Desactivar estadísticas para evitar errores de permisos
os.environ['STREAMLIT_GATHER_USAGE_STATS'] = 'false'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Registro de Limpieza",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Intentar importar reportlab silenciosamente
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    # Intentar instalar reportlab solo si no está disponible
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Reintentar importación después de la instalación
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        PDF_AVAILABLE = True
    except:
        PDF_AVAILABLE = False

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        color: #155724;
    }
    .warning-message {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        color: #856404;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# FUNCIÓN MEJORADA PARA GENERAR PDF
def generate_pdf_report(records, week_dates):
    try:
        if not PDF_AVAILABLE:
            raise ImportError("reportlab no está disponible")
            
        # Crear directorio de reportes si no existe
        os.makedirs("reportes", exist_ok=True)
        
        # Nombre del archivo
        pdf_path = f"reportes/reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf"
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Contenido del PDF
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4')
        )
        title = Paragraph("REPORTE SEMANAL DE LIMPIEZA", title_style)
        story.append(title)
        
        # Información de la semana
        week_info_style = ParagraphStyle(
            'WeekInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        week_info = Paragraph(
            f"Semana del {week_dates[0].strftime('%d/%m/%Y')} al {week_dates[-1].strftime('%d/%m/%Y')}", 
            week_info_style
        )
        story.append(week_info)
        
        story.append(Spacer(1, 20))
        
        # Preparar datos para la tabla
        if records:
            # Encabezados de la tabla
            table_data = [['Fecha', 'Día', 'Estudiantes', 'Área', 'Hora']]
            
            for record in records:
                # Limpiar caracteres problemáticos
                estudiantes = ', '.join(record['estudiantes'])
                # Reemplazar caracteres especiales
                estudiantes = estudiantes.replace('•', '-').replace('–', '-').replace('—', '-')
                
                fecha_obj = datetime.strptime(record['fecha'], '%Y-%m-%d')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                
                table_data.append([
                    fecha_formateada,
                    record['dia_semana'],
                    estudiantes,
                    record['tipo_limpieza'],
                    record['hora']
                ])
            
            # Crear tabla
            table = Table(table_data, colWidths=[70, 60, 180, 60, 50])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e86ab')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            
            # Estadísticas
            story.append(Spacer(1, 25))
            
            stats_style = ParagraphStyle(
                'Stats',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20
            )
            
            total_registros = len(records)
            limpiezas_aula = len([r for r in records if r['tipo_limpieza'] == 'Aula'])
            limpiezas_banos = len([r for r in records if r['tipo_limpieza'] == 'Baños'])
            
            stats_text = f"""
            <b>ESTADÍSTICAS:</b><br/>
            • Total de registros: {total_registros}<br/>
            • Limpiezas de aula: {limpiezas_aula}<br/>
            • Limpiezas de baños: {limpiezas_banos}<br/>
            """
            stats = Paragraph(stats_text, stats_style)
            story.append(stats)
        else:
            # Mensaje cuando no hay registros
            no_data_style = ParagraphStyle(
                'NoData',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
            no_data = Paragraph("No hay registros de limpieza para esta semana.", no_data_style)
            story.append(no_data)
        
        # Pie de página
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        footer = Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Sistema de Registro de Limpieza", 
            footer_style
        )
        story.append(footer)
        
        # Generar PDF
        doc.build(story)
        return pdf_path
        
    except Exception as e:
        st.error(f"Error detallado al generar PDF: {str(e)}")
        return None

# FUNCIONES PARA MANEJO DE DATOS
def load_data(filename):
    try:
        filepath = f"data/{filename}"
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

def save_data(data, filename):
    try:
        os.makedirs("data", exist_ok=True)
        with open(f"data/{filename}", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def initialize_session_state():
    if 'students' not in st.session_state:
        st.session_state.students = load_data("students.json")
    if 'cleaning_history' not in st.session_state:
        st.session_state.cleaning_history = load_data("cleaning_history.json")
    # Estado para edición
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

def get_current_week_dates():
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    return [start_of_week + pd.Timedelta(days=i) for i in range(5)]

# FUNCIÓN PARA ACTUALIZAR REGISTROS DE LIMPIEZA CUANDO SE ELIMINA UN ESTUDIANTE
def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece"""
    updated_records = []
    for record in st.session_state.cleaning_history:
        # Filtrar el estudiante eliminado de la lista de estudiantes
        updated_students = [s for s in record['estudiantes'] if s != student_name]
        
        # Solo mantener el registro si todavía tiene estudiantes
        if updated_students:
            record['estudiantes'] = updated_students
            updated_records.append(record)
    
    return updated_records

# FUNCIÓN PARA ACTUALIZAR REGISTROS DE LIMPIEZA CUANDO SE EDITA UN ESTUDIANTE
def update_cleaning_records_after_edit(old_name, new_name):
    """Actualiza el nombre del estudiante en todos los registros de limpieza"""
    for record in st.session_state.cleaning_history:
        if old_name in record['estudiantes']:
            # Reemplazar el nombre antiguo por el nuevo
            record['estudiantes'] = [new_name if s == old_name else s for s in record['estudiantes']]

initialize_session_state()

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una sección:", 
                       ["🏠 Inicio", "👥 Registro de Estudiantes", "📝 Registro de Limpieza", "📊 Historial de Limpieza"])

# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Bienvenido al Sistema de Registro de Limpieza</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Estudiantes", len(st.session_state.students))
    col2.metric("Registros de Limpieza", len(st.session_state.cleaning_history))
    
    week_records = []
    try:
        week_dates = get_current_week_dates()
        week_records = [r for r in st.session_state.cleaning_history 
                       if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
    except:
        week_records = []
    col3.metric("Limpiezas Esta Semana", len(week_records))
    
    # Resumen de limpiezas de la semana actual
    st.subheader("📅 Resumen de Limpiezas - Semana Actual")
    
    try:
        week_dates = get_current_week_dates()
        week_summary = []
        for day_date in week_dates:
            day_name = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][day_date.weekday()]
            day_records = [r for r in st.session_state.cleaning_history 
                          if datetime.strptime(r['fecha'], '%Y-%m-%d').date() == day_date]
            for record in day_records:
                week_summary.append({
                    'Día': day_name,
                    'Fecha': day_date.strftime('%d/%m/%Y'),
                    'Estudiantes': ', '.join(record['estudiantes']),
                    'Área': record['tipo_limpieza'],
                    'Hora': record['hora']
                })
        if week_summary:
            df_week = pd.DataFrame(week_summary)
            st.dataframe(df_week, use_container_width=True)
        else:
            st.info("No hay registros de limpieza para esta semana.")
    except Exception as e:
        st.error(f"Error al cargar el resumen semanal: {e}")

# Página de Registro de Estudiantes
elif page == "👥 Registro de Estudiantes":
    st.markdown('<h2 class="section-header">👥 Gestión de Estudiantes</h2>', unsafe_allow_html=True)
    
    # Formulario para agregar/editar estudiantes
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.edit_mode and st.session_state.editing_student:
                # Modo edición
                student_name = st.text_input(
                    "Nombre completo del estudiante:",
                    value=st.session_state.editing_student['nombre'],
                    key="edit_student_name"
                )
            else:
                # Modo agregar
                student_name = st.text_input("Nombre completo del estudiante:", key="student_name")
        
        with col2:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_id = st.text_input(
                    "ID o Matrícula:",
                    value=st.session_state.editing_student['id'],
                    key="edit_student_id"
                )
            else:
                student_id = st.text_input("ID o Matrícula (opcional):", key="student_id")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.edit_mode:
                submitted = st.form_submit_button("💾 Guardar Cambios")
            else:
                submitted = st.form_submit_button("👤 Agregar Estudiante")
        
        with col2:
            if st.session_state.edit_mode:
                if st.form_submit_button("❌ Cancelar Edición"):
                    st.session_state.edit_mode = False
                    st.session_state.editing_student = None
                    st.rerun()
        
        if submitted:
            if student_name.strip():
                student_name = student_name.strip().upper()
                
                if st.session_state.edit_mode:
                    # MODO EDICIÓN
                    old_name = st.session_state.editing_student['nombre']
                    old_id = st.session_state.editing_student['id']
                    
                    # Verificar si el nuevo nombre ya existe (excluyendo el actual)
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s['nombre'] != old_name]
                    if student_name.upper() in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        # Actualizar el estudiante
                        for student in st.session_state.students:
                            if student['nombre'] == old_name:
                                student['nombre'] = student_name
                                student['id'] = student_id.strip() if student_id else old_id
                                student['fecha_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                break
                        
                        # Actualizar registros de limpieza
                        update_cleaning_records_after_edit(old_name, student_name)
                        
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                        else:
                            st.error("❌ Error al guardar los cambios.")
                else:
                    # MODO AGREGAR
                    existing_students = [s['nombre'].upper() for s in st.session_state.students]
                    if student_name.upper() in existing_students:
                        st.error("❌ Este estudiante ya está registrado.")
                    else:
                        new_student = {
                            'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                            'nombre': student_name,
                            'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.students.append(new_student)
                        if save_data(st.session_state.students, "students.json"):
                            st.success("✅ Estudiante registrado exitosamente!")
                        else:
                            st.error("❌ Error al guardar el estudiante.")
            else:
                st.error("❌ Por favor ingresa un nombre válido.")
    
    # Lista de estudiantes registrados
    st.markdown('<h2 class="section-header">📋 Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        # Mostrar tabla de estudiantes
        students_df = pd.DataFrame(st.session_state.students)
        
        # Agregar columna de acciones
        display_df = students_df[['nombre', 'id']].copy()
        display_df['Acciones'] = "Editar | Eliminar"
        
        st.dataframe(display_df, use_container_width=True)
        
        # Gestión de estudiantes (Editar/Eliminar)
        st.markdown("### 🔧 Gestión de Estudiantes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✏️ Editar Estudiante")
            student_to_edit = st.selectbox(
                "Selecciona un estudiante para editar:",
                [s['nombre'] for s in st.session_state.students],
                key="edit_select"
            )
            
            if st.button("📝 Editar Estudiante", key="edit_button"):
                student = next((s for s in st.session_state.students if s['nombre'] == student_to_edit), None)
                if student:
                    st.session_state.editing_student = student
                    st.session_state.edit_mode = True
                    st.rerun()
        
        with col2:
            st.subheader("🗑️ Eliminar Estudiante")
            student_to_delete = st.selectbox(
                "Selecciona un estudiante para eliminar:",
                [s['nombre'] for s in st.session_state.students],
                key="delete_select"
            )
            
            # Mostrar información de confirmación
            if student_to_delete:
                # Contar en cuántos registros de limpieza aparece
                cleaning_count = sum(1 for record in st.session_state.cleaning_history 
                                   if student_to_delete in record['estudiantes'])
                
                st.warning(f"⚠️ **Advertencia:** Este estudiante aparece en **{cleaning_count}** registros de limpieza.")
                
                if cleaning_count > 0:
                    st.info("💡 **Nota:** El estudiante será eliminado de todos los registros de limpieza donde aparece.")
            
            if st.button("❌ Eliminar Estudiante", type="secondary", key="delete_button"):
                # Confirmación adicional para eliminación
                if cleaning_count > 0:
                    st.error("🚨 **¡ADVERTENCIA!** Esta acción no se puede deshacer.")
                    confirm = st.checkbox("✅ Confirmo que quiero eliminar este estudiante y quitarlo de todos los registros de limpieza")
                    
                    if confirm and st.button("🔥 CONFIRMAR ELIMINACIÓN", type="primary"):
                        # Eliminar estudiante
                        st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]
                        
                        # Actualizar registros de limpieza
                        st.session_state.cleaning_history = update_cleaning_records_after_deletion(student_to_delete)
                        
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante eliminado exitosamente!")
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar el estudiante.")
                else:
                    # Si no aparece en registros, eliminar directamente
                    st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]
                    
                    if save_data(st.session_state.students, "students.json"):
                        st.success("✅ Estudiante eliminado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el estudiante.")
    
    else:
        st.info("📝 No hay estudiantes registrados aún.")

# Página de Registro de Limpieza
elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 class="section-header">📝 Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    
    with st.form("cleaning_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today(), key="cleaning_date")
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"], key="cleaning_type")
        with col2:
            available_students = [s['nombre'] for s in st.session_state.students]
            st.write("Selecciona los estudiantes (1-3):")
            student1 = st.selectbox("Estudiante 1:", [""] + available_students, key="student1")
            student2 = st.selectbox("Estudiante 2 (opcional):", [""] + available_students, key="student2")
            student3 = st.selectbox("Estudiante 3 (opcional):", [""] + available_students, key="student3")
        submitted = st.form_submit_button("Registrar Limpieza")
        
        if submitted:
            students_selected = [s for s in [student1, student2, student3] if s.strip()]
            if not students_selected:
                st.error("❌ Debes seleccionar al menos un estudiante.")
            else:
                all_registered = all(student in available_students for student in students_selected)
                if not all_registered:
                    st.error("❌ Uno o más estudiantes no están registrados. Por favor regístralos primero.")
                else:
                    new_record = {
                        'fecha': cleaning_date.strftime('%Y-%m-%d'),
                        'dia_semana': ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][cleaning_date.weekday()],
                        'hora': datetime.now().strftime('%H:%M:%S'),
                        'estudiantes': students_selected,
                        'tipo_limpieza': cleaning_type,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.cleaning_history.append(new_record)
                    if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                        st.success("✅ Limpieza registrada exitosamente!")
                        st.balloons()
                    else:
                        st.error("❌ Error al guardar el registro de limpieza.")

# Página de Historial de Limpieza
elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 class="section-header">📊 Historial de Limpieza</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"], key="filter_type")
    with col2:
        date_range = st.date_input(
            "Rango de fechas:",
            value=(date.today() - pd.Timedelta(days=7), date.today()),
            max_value=date.today(),
            key="date_range"
        )
    with col3:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

    filtered_history = st.session_state.cleaning_history.copy()
    if filter_type != "Todos":
        filtered_history = [r for r in filtered_history if r['tipo_limpieza'] == filter_type]
    try:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered_history = [
                r for r in filtered_history 
                if start_date <= datetime.strptime(r['fecha'], '%Y-%m-%d').date() <= end_date
            ]
    except:
        pass

    if filtered_history:
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        st.dataframe(display_df, use_container_width=True)

        st.subheader("📈 Estadísticas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(filtered_history))
        col2.metric("Limpiezas de Aula", len([r for r in filtered_history if r['tipo_limpieza'] == 'Aula']))
        col3.metric("Limpiezas de Baños", len([r for r in filtered_history if r['tipo_limpieza'] == 'Baños']))

        st.subheader("📄 Generar Reporte PDF")
        
        if not PDF_AVAILABLE:
            st.error("""
            **reportlab no está instalado. Para generar PDFs, ejecuta:**
            ```bash
            pip install reportlab
            ```
            """)
        else:
            if st.button("📥 Descargar Reporte Semanal en PDF"):
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history 
                                  if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
                    
                    if week_records:
                        with st.spinner("Generando PDF..."):
                            pdf_path = generate_pdf_report(week_records, week_dates)
                        
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            
                            st.success("✅ PDF generado exitosamente!")
                            
                            # Botón de descarga
                            st.download_button(
                                label="📄 Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf",
                                mime="application/pdf",
                                key="download_pdf"
                            )
                        else:
                            st.error("❌ No se pudo generar el archivo PDF.")
                    else:
                        st.warning("⚠️ No hay registros de limpieza para esta semana.")
                except Exception as e:
                    st.error(f"❌ Error al generar el PDF: {str(e)}")

    else:
        st.info("No hay registros de limpieza que coincidan con los filtros seleccionados.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:#666; font-size:0.10em;'>
        <p>Sistema de Registro de Limpieza 🧹</p>
        <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
    </div>
    """,
    unsafe_allow_html=Trueimport streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import os
import base64

# SOLUCIÓN: Desactivar estadísticas para evitar errores de permisos
os.environ['STREAMLIT_GATHER_USAGE_STATS'] = 'false'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Registro de Limpieza",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Intentar importar reportlab silenciosamente
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    # Intentar instalar reportlab solo si no está disponible
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Reintentar importación después de la instalación
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        PDF_AVAILABLE = True
    except:
        PDF_AVAILABLE = False

# Estilos CSS minimalistas y profesionales
st.markdown("""
<style>
    /* Fondo blanco limpio */
    .stApp {
        background-color: #ffffff;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    
    /* Header principal elegante */
    .main-header {
        font-size: 2.5rem;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: -0.5px;
        padding: 1rem 0;
        border-bottom: 1px solid #eaeaea;
    }
    
    /* Headers de sección */
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        font-weight: 500;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
    }
    
    /* Tarjetas de métricas limpias */
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: #007bff;
        transform: translateY(-2px);
    }
    
    .metric-card h3 {
        color: #6c757d;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        color: #1a1a1a;
        font-size: 2rem;
        margin: 0;
        font-weight: 600;
    }
    
    /* Botones minimalistas */
    .stButton button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        background-color: #0056b3;
        transform: translateY(-1px);
    }
    
    /* Botones secundarios */
    .stButton button[kind="secondary"] {
        background-color: #6c757d;
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: #545b62;
    }
    
    /* Formularios limpios */
    .stForm {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    /* Mensajes de estado */
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 6px;
        color: #155724;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        color: #856404;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 6px;
        color: #721c24;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Dataframes limpios */
    .dataframe {
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #e9ecef;
    }
    
    /* Inputs y selects */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        border-radius: 6px !important;
        border: 1px solid #ced4da !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stDateInput input:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1) !important;
    }
    
    /* Sidebar minimalista */
    .css-1d391kg {
        background: #f8f9fa !important;
        border-right: 1px solid #e9ecef !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: white;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #e9ecef;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    
    /* Footer limpio */
    .footer {
        text-align: center;
        color: #6c757d;
        padding: 2rem;
        margin-top: 3rem;
        font-size: 0.9em;
        border-top: 1px solid #eaeaea;
    }
</style>
""", unsafe_allow_html=True)

# FUNCIÓN MEJORADA PARA GENERAR PDF
def generate_pdf_report(records, week_dates):
    try:
        if not PDF_AVAILABLE:
            raise ImportError("reportlab no está disponible")
            
        # Crear directorio de reportes si no existe
        os.makedirs("reportes", exist_ok=True)
        
        # Nombre del archivo
        pdf_path = f"reportes/reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf"
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Contenido del PDF
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4')
        )
        title = Paragraph("REPORTE SEMANAL DE LIMPIEZA", title_style)
        story.append(title)
        
        # Información de la semana
        week_info_style = ParagraphStyle(
            'WeekInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        week_info = Paragraph(
            f"Semana del {week_dates[0].strftime('%d/%m/%Y')} al {week_dates[-1].strftime('%d/%m/%Y')}", 
            week_info_style
        )
        story.append(week_info)
        
        story.append(Spacer(1, 20))
        
        # Preparar datos para la tabla
        if records:
            # Encabezados de la tabla
            table_data = [['Fecha', 'Día', 'Estudiantes', 'Área', 'Hora']]
            
            for record in records:
                # Limpiar caracteres problemáticos
                estudiantes = ', '.join(record['estudiantes'])
                # Reemplazar caracteres especiales
                estudiantes = estudiantes.replace('•', '-').replace('–', '-').replace('—', '-')
                
                fecha_obj = datetime.strptime(record['fecha'], '%Y-%m-%d')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                
                table_data.append([
                    fecha_formateada,
                    record['dia_semana'],
                    estudiantes,
                    record['tipo_limpieza'],
                    record['hora']
                ])
            
            # Crear tabla
            table = Table(table_data, colWidths=[70, 60, 180, 60, 50])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e86ab')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            
            # Estadísticas
            story.append(Spacer(1, 25))
            
            stats_style = ParagraphStyle(
                'Stats',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20
            )
            
            total_registros = len(records)
            limpiezas_aula = len([r for r in records if r['tipo_limpieza'] == 'Aula'])
            limpiezas_banos = len([r for r in records if r['tipo_limpieza'] == 'Baños'])
            
            stats_text = f"""
            <b>ESTADÍSTICAS:</b><br/>
            • Total de registros: {total_registros}<br/>
            • Limpiezas de aula: {limpiezas_aula}<br/>
            • Limpiezas de baños: {limpiezas_banos}<br/>
            """
            stats = Paragraph(stats_text, stats_style)
            story.append(stats)
        else:
            # Mensaje cuando no hay registros
            no_data_style = ParagraphStyle(
                'NoData',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
            no_data = Paragraph("No hay registros de limpieza para esta semana.", no_data_style)
            story.append(no_data)
        
        # Pie de página
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        footer = Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Sistema de Registro de Limpieza", 
            footer_style
        )
        story.append(footer)
        
        # Generar PDF
        doc.build(story)
        return pdf_path
        
    except Exception as e:
        st.error(f"Error detallado al generar PDF: {str(e)}")
        return None

# FUNCIONES PARA MANEJO DE DATOS
def load_data(filename):
    try:
        filepath = f"data/{filename}"
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

def save_data(data, filename):
    try:
        os.makedirs("data", exist_ok=True)
        with open(f"data/{filename}", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def initialize_session_state():
    if 'students' not in st.session_state:
        st.session_state.students = load_data("students.json")
    if 'cleaning_history' not in st.session_state:
        st.session_state.cleaning_history = load_data("cleaning_history.json")
    # Estado para edición
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

def get_current_week_dates():
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    return [start_of_week + pd.Timedelta(days=i) for i in range(5)]

# FUNCIÓN PARA ACTUALIZAR REGISTROS DE LIMPIEZA CUANDO SE ELIMINA UN ESTUDIANTE
def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece"""
    updated_records = []
    for record in st.session_state.cleaning_history:
        # Filtrar el estudiante eliminado de la lista de estudiantes
        updated_students = [s for s in record['estudiantes'] if s != student_name]
        
        # Solo mantener el registro si todavía tiene estudiantes
        if updated_students:
            record['estudiantes'] = updated_students
            updated_records.append(record)
    
    return updated_records

# FUNCIÓN PARA ACTUALIZAR REGISTROS DE LIMPIEZA CUANDO SE EDITA UN ESTUDIANTE
def update_cleaning_records_after_edit(old_name, new_name):
    """Actualiza el nombre del estudiante en todos los registros de limpieza"""
    for record in st.session_state.cleaning_history:
        if old_name in record['estudiantes']:
            # Reemplazar el nombre antiguo por el nuevo
            record['estudiantes'] = [new_name if s == old_name else s for s in record['estudiantes']]

initialize_session_state()

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una sección:", 
                       ["🏠 Inicio", "👥 Estudiantes", "📝 Limpieza", "📊 Reportes"])

# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Dashboard Principal</h2>', unsafe_allow_html=True)
    
    # Métricas en tarjetas limpias
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Estudiantes</h3>
            <h2>{len(st.session_state.students)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Registros Totales</h3>
            <h2>{len(st.session_state.cleaning_history)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        week_records = []
        try:
            week_dates = get_current_week_dates()
            week_records = [r for r in st.session_state.cleaning_history 
                           if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
        except:
            week_records = []
        st.markdown(f"""
        <div class="metric-card">
            <h3>Esta Semana</h3>
            <h2>{len(week_records)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen de limpiezas de la semana actual
    st.markdown('<h2 class="section-header">Resumen Semanal</h2>', unsafe_allow_html=True)
    
    try:
        week_dates = get_current_week_dates()
        week_summary = []
        for day_date in week_dates:
            day_name = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][day_date.weekday()]
            day_records = [r for r in st.session_state.cleaning_history 
                          if datetime.strptime(r['fecha'], '%Y-%m-%d').date() == day_date]
            for record in day_records:
                week_summary.append({
                    'Día': day_name,
                    'Fecha': day_date.strftime('%d/%m/%Y'),
                    'Estudiantes': ', '.join(record['estudiantes']),
                    'Área': record['tipo_limpieza'],
                    'Hora': record['hora']
                })
        if week_summary:
            df_week = pd.DataFrame(week_summary)
            st.dataframe(df_week, use_container_width=True)
        else:
            st.info("No hay registros de limpieza para esta semana.")
    except Exception as e:
        st.error(f"Error al cargar el resumen semanal: {e}")

# Página de Estudiantes
elif page == "👥 Estudiantes":
    st.markdown('<h2 class="section-header">Gestión de Estudiantes</h2>', unsafe_allow_html=True)
    
    # Formulario para agregar/editar estudiantes
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.edit_mode and st.session_state.editing_student:
                # Modo edición
                student_name = st.text_input(
                    "Nombre completo del estudiante:",
                    value=st.session_state.editing_student['nombre'],
                    key="edit_student_name"
                )
            else:
                # Modo agregar
                student_name = st.text_input("Nombre completo del estudiante:", key="student_name")
        
        with col2:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_id = st.text_input(
                    "ID o Matrícula:",
                    value=st.session_state.editing_student['id'],
                    key="edit_student_id"
                )
            else:
                student_id = st.text_input("ID o Matrícula (opcional):", key="student_id")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.edit_mode:
                submitted = st.form_submit_button("💾 Guardar Cambios")
            else:
                submitted = st.form_submit_button("👤 Agregar Estudiante")
        
        with col2:
            if st.session_state.edit_mode:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state.edit_mode = False
                    st.session_state.editing_student = None
                    st.rerun()
        
        if submitted:
            if student_name.strip():
                student_name = student_name.strip().upper()
                
                if st.session_state.edit_mode:
                    # MODO EDICIÓN
                    old_name = st.session_state.editing_student['nombre']
                    old_id = st.session_state.editing_student['id']
                    
                    # Verificar si el nuevo nombre ya existe (excluyendo el actual)
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s['nombre'] != old_name]
                    if student_name.upper() in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        # Actualizar el estudiante
                        for student in st.session_state.students:
                            if student['nombre'] == old_name:
                                student['nombre'] = student_name
                                student['id'] = student_id.strip() if student_id else old_id
                                student['fecha_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                break
                        
                        # Actualizar registros de limpieza
                        update_cleaning_records_after_edit(old_name, student_name)
                        
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                        else:
                            st.error("❌ Error al guardar los cambios.")
                else:
                    # MODO AGREGAR
                    existing_students = [s['nombre'].upper() for s in st.session_state.students]
                    if student_name.upper() in existing_students:
                        st.error("❌ Este estudiante ya está registrado.")
                    else:
                        new_student = {
                            'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                            'nombre': student_name,
                            'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.students.append(new_student)
                        if save_data(st.session_state.students, "students.json"):
                            st.success("✅ Estudiante registrado exitosamente!")
                        else:
                            st.error("❌ Error al guardar el estudiante.")
            else:
                st.error("❌ Por favor ingresa un nombre válido.")
    
    # Lista de estudiantes registrados
    st.markdown('<h2 class="section-header">Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        # Mostrar tabla de estudiantes
        students_df = pd.DataFrame(st.session_state.students)
        st.dataframe(students_df[['nombre', 'id']], use_container_width=True)
        
        # Gestión de estudiantes (Editar/Eliminar)
        st.markdown("### Gestión de Estudiantes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Editar Estudiante")
            student_to_edit = st.selectbox(
                "Selecciona un estudiante para editar:",
                [s['nombre'] for s in st.session_state.students],
                key="edit_select"
            )
            
            if st.button("✏️ Editar Estudiante", key="edit_button"):
                student = next((s for s in st.session_state.students if s['nombre'] == student_to_edit), None)
                if student:
                    st.session_state.editing_student = student
                    st.session_state.edit_mode = True
                    st.rerun()
        
        with col2:
            st.subheader("Eliminar Estudiante")
            student_to_delete = st.selectbox(
                "Selecciona un estudiante para eliminar:",
                [s['nombre'] for s in st.session_state.students],
                key="delete_select"
            )
            
            # Mostrar información de confirmación
            if student_to_delete:
                # Contar en cuántos registros de limpieza aparece
                cleaning_count = sum(1 for record in st.session_state.cleaning_history 
                                   if student_to_delete in record['estudiantes'])
                
                if cleaning_count > 0:
                    st.warning(f"Este estudiante aparece en {cleaning_count} registros de limpieza.")
            
            if st.button("🗑️ Eliminar Estudiante", type="secondary", key="delete_button"):
                # Confirmación adicional para eliminación
                if cleaning_count > 0:
                    confirm = st.checkbox("Confirmar eliminación (se eliminará de todos los registros)")
                    
                    if confirm and st.button("✅ Confirmar Eliminación"):
                        # Eliminar estudiante
                        st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]
                        
                        # Actualizar registros de limpieza
                        st.session_state.cleaning_history = update_cleaning_records_after_deletion(student_to_delete)
                        
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante eliminado exitosamente!")
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar el estudiante.")
                else:
                    # Si no aparece en registros, eliminar directamente
                    st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]
                    
                    if save_data(st.session_state.students, "students.json"):
                        st.success("✅ Estudiante eliminado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el estudiante.")
    
    else:
        st.info("No hay estudiantes registrados aún.")

# Página de Limpieza
elif page == "📝 Limpieza":
    st.markdown('<h2 class="section-header">Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    
    with st.form("cleaning_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today(), key="cleaning_date")
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"], key="cleaning_type")
        with col2:
            available_students = [s['nombre'] for s in st.session_state.students]
            st.write("Selecciona los estudiantes (1-3):")
            student1 = st.selectbox("Estudiante 1:", [""] + available_students, key="student1")
            student2 = st.selectbox("Estudiante 2 (opcional):", [""] + available_students, key="student2")
            student3 = st.selectbox("Estudiante 3 (opcional):", [""] + available_students, key="student3")
        submitted = st.form_submit_button("Registrar Limpieza")
        
        if submitted:
            students_selected = [s for s in [student1, student2, student3] if s.strip()]
            if not students_selected:
                st.error("❌ Debes seleccionar al menos un estudiante.")
            else:
                all_registered = all(student in available_students for student in students_selected)
                if not all_registered:
                    st.error("❌ Uno o más estudiantes no están registrados. Por favor regístralos primero.")
                else:
                    new_record = {
                        'fecha': cleaning_date.strftime('%Y-%m-%d'),
                        'dia_semana': ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][cleaning_date.weekday()],
                        'hora': datetime.now().strftime('%H:%M:%S'),
                        'estudiantes': students_selected,
                        'tipo_limpieza': cleaning_type,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.cleaning_history.append(new_record)
                    if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                        st.success("✅ Limpieza registrada exitosamente!")
                        st.balloons()
                    else:
                        st.error("❌ Error al guardar el registro de limpieza.")

# Página de Reportes
elif page == "📊 Reportes":
    st.markdown('<h2 class="section-header">Historial y Reportes</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"], key="filter_type")
    with col2:
        date_range = st.date_input(
            "Rango de fechas:",
            value=(date.today() - pd.Timedelta(days=7), date.today()),
            max_value=date.today(),
            key="date_range"
        )
    with col3:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

    filtered_history = st.session_state.cleaning_history.copy()
    if filter_type != "Todos":
        filtered_history = [r for r in filtered_history if r['tipo_limpieza'] == filter_type]
    try:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered_history = [
                r for r in filtered_history 
                if start_date <= datetime.strptime(r['fecha'], '%Y-%m-%d').date() <= end_date
            ]
    except:
        pass

    if filtered_history:
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        st.dataframe(display_df, use_container_width=True)

        st.subheader("Estadísticas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(filtered_history))
        col2.metric("Limpiezas de Aula", len([r for r in filtered_history if r['tipo_limpieza'] == 'Aula']))
        col3.metric("Limpiezas de Baños", len([r for r in filtered_history if r['tipo_limpieza'] == 'Baños']))

        st.subheader("Generar Reporte PDF")
        
        if not PDF_AVAILABLE:
            st.error("reportlab no está instalado. Ejecuta: pip install reportlab")
        else:
            if st.button("📥 Descargar Reporte Semanal"):
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history 
                                  if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
                    
                    if week_records:
                        with st.spinner("Generando PDF..."):
                            pdf_path = generate_pdf_report(week_records, week_dates)
                        
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            
                            st.success("✅ PDF generado exitosamente!")
                            
                            # Botón de descarga
                            st.download_button(
                                label="📄 Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf",
                                mime="application/pdf",
                                key="download_pdf"
                            )
                        else:
                            st.error("❌ No se pudo generar el archivo PDF.")
                    else:
                        st.warning("No hay registros de limpieza para esta semana.")
                except Exception as e:
                    st.error(f"❌ Error al generar el PDF: {str(e)}")

    else:
        st.info("No hay registros de limpieza que coincidan con los filtros seleccionados.")

# Footer
st.markdown("""
<div class="footer">
    <p>Sistema de Registro de Limpieza</p>
    <p>© 2025 ING. Irvin Adonis Mora Paredes</p>
</div>
""", unsafe_allow_html=True)
)