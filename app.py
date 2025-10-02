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

# Estilos CSS personalizados con fondo profesional
st.markdown("""
<style>
    /* Fondo profesional con gradiente suave */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Contenedor principal con efecto glassmorphism */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Sidebar profesional */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(15px) !important;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.7rem;
        margin: 2rem 0 1.5rem 0;
        font-weight: 600;
    }
    
    /* Tarjetas de métricas modernas */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #3498db;
        text-align: center;
        margin: 0.5rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card h3 {
        color: #7f8c8d;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .metric-card h2 {
        color: #2c3e50;
        font-size: 2.2rem;
        margin: 0;
        font-weight: 700;
    }
    
    /* Botones modernos */
    .stButton button {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
        background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
    }
    
    /* Botones secundarios */
    .stButton button[kind="secondary"] {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        box-shadow: 0 4px 15px rgba(149, 165, 166, 0.3);
    }
    
    .stButton button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%);
        box-shadow: 0 8px 25px rgba(149, 165, 166, 0.4);
    }
    
    /* Botones de éxito */
    .stButton button:contains("Agregar"), 
    .stButton button:contains("Guardar"), 
    .stButton button:contains("Registrar") {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
    }
    
    /* Formularios */
    .stForm {
        background: rgba(255, 255, 255, 0.8);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
    }
    
    /* Mensajes de estado mejorados */
    .success-message {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: none;
        border-radius: 10px;
        color: #155724;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(39, 174, 96, 0.2);
    }
    
    .warning-message {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: none;
        border-radius: 10px;
        color: #856404;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(255, 193, 7, 0.2);
    }
    
    .error-message {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: none;
        border-radius: 10px;
        color: #721c24;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(220, 53, 69, 0.2);
    }
    
    /* Dataframes estilizados */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        background: white;
    }
    
    /* Inputs y selects mejorados */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
        background: rgba(255, 255, 255, 0.9) !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stDateInput input:focus {
        border-color: #3498db !important;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
    }
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255,255,255,0.2) !important;
    }
    
    /* Radio buttons mejorados */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    /* Checkbox mejorado */
    .stCheckbox > label {
        background: rgba(255, 255, 255, 0.8);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }
    
    /* Expander mejorado */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* Footer profesional */
    .footer {
        text-align: center;
        color: white;
        padding: 2rem;
        margin-top: 3rem;
        font-size: 0.9em;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
            padding: 0.5rem;
        }
        
        .section-header {
            font-size: 1.5rem;
        }
        
        .metric-card {
            padding: 1rem;
            margin: 0.25rem;
        }
        
        .main-container {
            padding: 1rem;
            margin: 0.5rem;
        }
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

# Contenedor principal con fondo profesional
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Gestión de Limpieza</h1>', unsafe_allow_html=True)

# Sidebar para navegación
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                padding: 2rem; 
                border-radius: 15px; 
                color: white; 
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(52, 152, 219, 0.3);'>
        <h1 style='font-size: 3rem; margin: 0;'>🧹</h1>
        <h3 style='margin: 0.5rem 0;'>Sistema de Gestión</h3>
        <p style='margin: 0; font-size: 0.9em;'>Control de Limpieza</p>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "**Navegación**", 
        ["🏠 Inicio", "👥 Gestión de Estudiantes", "📝 Registro de Limpieza", "📊 Historial y Reportes"],
        key="navigation"
    )

# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">📊 Dashboard Principal</h2>', unsafe_allow_html=True)
    
    # Métricas en tarjetas modernas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Estudiantes</h3>
            <h2>{len(st.session_state.students)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📝 Registros Totales</h3>
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
            <h3>📅 Esta Semana</h3>
            <h2>{len(week_records)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen de limpiezas de la semana actual
    st.markdown('<h2 class="section-header">📋 Resumen Semanal de Limpiezas</h2>', unsafe_allow_html=True)
    
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

# Página de Gestión de Estudiantes
elif page == "👥 Gestión de Estudiantes":
    st.markdown('<h2 class="section-header">👤 Gestión de Estudiantes</h2>', unsafe_allow_html=True)
    
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
        submitted = st.form_submit_button("🧹 Registrar Limpieza")
        
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

# Página de Historial y Reportes
elif page == "📊 Historial y Reportes":
    st.markdown('<h2 class="section-header">📊 Historial y Reportes de Limpieza</h2>', unsafe_allow_html=True)
    
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

st.markdown('</div>', unsafe_allow_html=True)

# Footer profesional
st.markdown("""
<div class="footer">
    <p>Sistema de Gestión de Limpieza 🧹</p>
    <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
</div>
""", unsafe_allow_html=True)