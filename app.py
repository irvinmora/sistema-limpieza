# app.py
import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import base64
import pytz
import tempfile

# SOLUCIÓN: Desactivar estadísticas para evitar errores de permisos
os.environ['STREAMLIT_GATHER_USAGE_STATS'] = 'false'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Configuración de zona horaria de Ecuador
ECUADOR_TZ = pytz.timezone('America/Guayaquil')

def get_today_ecuador():
    """Retorna la fecha actual en zona horaria de Ecuador"""
    return datetime.now(ECUADOR_TZ).date()

def get_now_ecuador():
    """Retorna datetime actual en zona horaria de Ecuador"""
    return datetime.now(ECUADOR_TZ)

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
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        PDF_AVAILABLE = True
    except Exception:
        PDF_AVAILABLE = False

# Estilos CSS personalizados y responsivos
st.markdown("""
<style>
    /* Estilos base responsivos */
    .main-header {
        font-size: 2.5rem;
        color: red;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }
    
    .section-header {
        font-size: 1.8rem;
        color: blue;
        border-bottom: 3px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    .success-message {
        padding: 1rem;
        background-color: #fce5cd;
        border: 2px solid #c3e6cb;
        border-radius: 1rem;
        color: #155724;
        margin: 1rem 0;
    }
    
    .warning-message {
        padding: 1rem;
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 0.5rem;
        color: #856404;
        margin: 1rem 0;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        color: #721c24;
        margin: 1rem 0;
    }
    
    /* Sidebar responsiva */
    @media (max-width: 768px) {
        .css-1d391kg {
            transition: transform 0.3s ease;
        }
        
        .main-header {
            font-size: 2rem;
            margin-top: 3rem;
        }
        
        .section-header {
            font-size: 1.5rem;
        }
        
        /* Ajustes para columnas en móviles */
        .row-widget.stColumns {
            flex-direction: column;
        }
        
        .row-widget.stColumns > div {
            width: 100% !important;
            margin-bottom: 1rem;
        }
        
        /* Ajustes para métricas */
        .element-container .stMetric {
            margin-bottom: 1rem;
        }
        
        /* Ajustes para formularios */
        .stForm {
            padding: 1rem;
        }
        
        /* Ajustes para dataframes */
        .dataframe {
            font-size: 0.8rem;
        }
        
        /* Ajustes para botones */
        .stButton button {
            padding: 0.8rem 1rem;
            font-size: 0.9rem;
        }
    }
    
    /* Tablets */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main-header {
            font-size: 2.2rem;
        }
        
        .section-header {
            font-size: 1.6rem;
        }
    }
    
    /* Mejoras para inputs en móviles */
    @media (max-width: 768px) {
        .stTextInput input, 
        .stSelectbox select, 
        .stDateInput input {
            font-size: 16px !important; /* Previene zoom en iOS */
            padding: 12px !important;
        }
    }
    
    /* Mejoras para la sidebar */
    .css-1d391kg {
        background: #f8f9fa !important;
        border-right: 1px solid #e9ecef !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# FUNCIONES PARA PDF & REPORTES
# -------------------------
def generate_pdf_report(records, week_dates):
    try:
        if not PDF_AVAILABLE:
            raise ImportError("reportlab no está disponible")
            
        os.makedirs("reportes", exist_ok=True)
        today_ecuador = get_today_ecuador()
        pdf_path = f"reportes/reporte_limpieza_semana_{today_ecuador.strftime('%Y-%m-%d')}.pdf"
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        styles = getSampleStyleSheet()
        
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
        
        if records:
            table_data = [['Fecha', 'Día', 'Estudiantes', 'Área', 'Hora']]
            for record in records:
                estudiantes = ', '.join(record['estudiantes'])
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
            no_data_style = ParagraphStyle(
                'NoData',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
            no_data = Paragraph("No hay registros de limpieza para esta semana.", no_data_style)
            story.append(no_data)
        
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        now_ecuador = get_now_ecuador()
        footer = Paragraph(
            f"Generado el {now_ecuador.strftime('%d/%m/%Y %H:%M:%S')} (Ecuador) - Sistema de Registro de Limpieza", 
            footer_style
        )
        story.append(footer)
        doc.build(story)
        return pdf_path
    except Exception as e:
        st.error(f"Error detallado al generar PDF: {str(e)}")
        return None

# -------------------------
# FUNCIONES DE CARGA / GUARDADO SEGURO
# -------------------------
DATA_DIR = "data"

def ensure_data_dir_and_files():
    """Asegura que exista la carpeta data y que los archivos JSON existan (vacíos si no)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for fname in ("students.json", "cleaning_history.json"):
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            except Exception as e:
                st.error(f"Error creando {path}: {e}")

def load_data(filename):
    """Carga datos desde data/filename, devolviendo lista ([]) si hay cualquier problema."""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            # crear archivo vacío si no existe
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        if os.path.getsize(filepath) == 0:
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except Exception:
        # Si algo falla, retornar lista vacía (no crash)
        return []

def save_data(data, filename):
    """Guarda de forma atómica el JSON en data/filename. Retorna True si OK, False si falla."""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        # Escribir en archivo temporal y reemplazar
        dirpath = os.path.dirname(filepath)
        os.makedirs(dirpath, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                json.dump(data, tmpf, ensure_ascii=False, indent=2)
            # Reemplaza el archivo destino
            os.replace(tmp_path, filepath)
        finally:
            # Si por alguna razón quedó el temporal, intentar eliminar
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        return True
    except Exception as e:
        st.error(f"Error al guardar {filename}: {e}")
        return False

# -------------------------
# ESTADO DE LA APP / INICIALIZACIÓN
# -------------------------
def initialize_session_state():
    ensure_data_dir_and_files()
    if 'students' not in st.session_state:
        st.session_state.students = load_data("students.json")
    if 'cleaning_history' not in st.session_state:
        st.session_state.cleaning_history = load_data("cleaning_history.json")
    # Estados para edición y confirmación
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = None

def get_current_week_dates():
    today = get_today_ecuador()
    start_of_week = today - timedelta(days=today.weekday())
    return [start_of_week + timedelta(days=i) for i in range(5)]

def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece.
       Si un registro queda sin estudiantes, se elimina ese registro."""
    updated_records = []
    for record in st.session_state.cleaning_history:
        updated_students = [s for s in record.get('estudiantes', []) if s != student_name]
        if updated_students:
            record['estudiantes'] = updated_students
            updated_records.append(record)
    return updated_records

def update_cleaning_records_after_edit(old_name, new_name):
    """Actualiza el nombre del estudiante en todos los registros de limpieza"""
    for record in st.session_state.cleaning_history:
        if old_name in record.get('estudiantes', []):
            record['estudiantes'] = [new_name if s == old_name else s for s in record['estudiantes']]

# Inicializamos el estado
initialize_session_state()

# -------------------------
# UI PRINCIPAL
# -------------------------
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)
today_ecuador = get_today_ecuador()
st.info(f"📅 Fecha actual: {today_ecuador.strftime('%d/%m/%Y')} - Hora de Ecuador")

with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: #007bff; color: white; border-radius: 10px; margin-bottom: 1rem;'>
        <h3>🧹 MENÚ PRINCIPAL</h3>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "**Navegación**", 
        ["🏠 Inicio", "👥 Estudiantes", "📝 Limpieza", "📊 Reportes"],
        key="navigation"
    )

# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Dashboard Principal</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Estudiantes", len(st.session_state.students))
    with col2:
        st.metric("Registros Totales", len(st.session_state.cleaning_history))
    with col3:
        week_records = []
        try:
            week_dates = get_current_week_dates()
            week_records = [r for r in st.session_state.cleaning_history 
                           if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
        except Exception:
            week_records = []
        st.metric("Limpiezas Esta Semana", len(week_records))
    
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
    
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_name = st.text_input(
                    "Nombre completo del estudiante:",
                    value=st.session_state.editing_student.get('nombre', ''),
                    key="edit_student_name"
                )
            else:
                student_name = st.text_input("Nombre completo del estudiante:", key="student_name")
        with col2:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_id = st.text_input(
                    "ID o Matrícula:",
                    value=st.session_state.editing_student.get('id', ''),
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
                    st.experimental_rerun()
        
        if submitted:
            # Validaciones básicas
            if not student_name or not student_name.strip():
                st.error("❌ Por favor ingresa un nombre válido.")
            else:
                student_name = student_name.strip().upper()
                if st.session_state.edit_mode and st.session_state.editing_student:
                    # MODO EDICIÓN
                    old_name = st.session_state.editing_student.get('nombre')
                    old_id = st.session_state.editing_student.get('id')
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s.get('nombre') != old_name]
                    if student_name.upper() in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        now_ecuador = get_now_ecuador()
                        updated = False
                        for student in st.session_state.students:
                            if student.get('nombre') == old_name:
                                student['nombre'] = student_name
                                student['id'] = student_id.strip() if student_id else old_id
                                student['fecha_actualizacion'] = now_ecuador.strftime('%Y-%m-%d %H:%M:%S')
                                updated = True
                                break
                        # Actualizar registros de limpieza
                        update_cleaning_records_after_edit(old_name, student_name)
                        # Guardar ambos archivos
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                            st.experimental_rerun()
                        else:
                            st.error("❌ Error al guardar los cambios.")
                else:
                    # MODO AGREGAR
                    existing_students = [s.get('nombre', '').upper() for s in st.session_state.students]
                    if student_name.upper() in existing_students:
                        st.error("❌ Este estudiante ya está registrado.")
                    else:
                        now_ecuador = get_now_ecuador()
                        new_student = {
                            'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                            'nombre': student_name,
                            'fecha_registro': now_ecuador.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.students.append(new_student)
                        if save_data(st.session_state.students, "students.json"):
                            st.success("✅ Estudiante registrado exitosamente!")
                            # Fuerza recarga para que el estado y selectboxes se actualicen
                            st.experimental_rerun()
                        else:
                            st.error("❌ Error al guardar el estudiante.")

    # Lista de estudiantes registrados
    st.markdown('<h2 class="section-header">Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        # Evitar KeyErrors: si no hay columnas, se manejan
        cols_to_show = [c for c in ['nombre', 'id'] if c in students_df.columns]
        st.dataframe(students_df[cols_to_show], use_container_width=True)
        
        st.markdown("### Gestión de Estudiantes")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Editar Estudiante")
            student_to_edit = st.selectbox(
                "Selecciona un estudiante para editar:",
                [s.get('nombre', '') for s in st.session_state.students],
                key="edit_select"
            )
            if st.button("✏️ Editar Estudiante", key="edit_button"):
                student = next((s for s in st.session_state.students if s.get('nombre') == student_to_edit), None)
                if student:
                    st.session_state.editing_student = student
                    st.session_state.edit_mode = True
                    st.experimental_rerun()
        with col2:
            st.subheader("Eliminar Estudiante")
            student_to_delete = st.selectbox(
                "Selecciona un estudiante para eliminar:",
                [s.get('nombre', '') for s in st.session_state.students],
                key="delete_select"
            )
            cleaning_count = 0
            if student_to_delete:
                cleaning_count = sum(1 for record in st.session_state.cleaning_history if student_to_delete in record.get('estudiantes', []))
                if cleaning_count > 0:
                    st.warning(f"⚠️ Este estudiante aparece en {cleaning_count} registro(s) de limpieza.")
                    st.info("💡 Al eliminar, se removerá de todos los registros de limpieza automáticamente.")
            if st.session_state.confirm_delete == student_to_delete:
                st.error(f"⚠️ ¿Estás seguro de eliminar a **{student_to_delete}**?")
                if cleaning_count > 0:
                    st.warning(f"Se eliminará de {cleaning_count} registro(s) de limpieza.")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Sí, eliminar", key="confirm_yes", type="primary"):
                        st.session_state.students = [s for s in st.session_state.students if s.get('nombre') != student_to_delete]
                        st.session_state.cleaning_history = update_cleaning_records_after_deletion(student_to_delete)
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.session_state.confirm_delete = None
                            st.success(f"✅ Estudiante '{student_to_delete}' eliminado exitosamente!")
                            if cleaning_count > 0:
                                st.success(f"✅ Removido de {cleaning_count} registro(s) de limpieza.")
                            st.experimental_rerun()
                        else:
                            st.error("❌ Error al eliminar el estudiante.")
                            st.session_state.confirm_delete = None
                with col_b:
                    if st.button("❌ Cancelar", key="confirm_no"):
                        st.session_state.confirm_delete = None
                        st.experimental_rerun()
            else:
                if st.button("🗑️ Eliminar Estudiante", type="secondary", key="delete_button"):
                    st.session_state.confirm_delete = student_to_delete
                    st.experimental_rerun()
    else:
        st.info("No hay estudiantes registrados aún.")

# Página de Limpieza
elif page == "📝 Limpieza":
    st.markdown('<h2 class="section-header">Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    with st.form("cleaning_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            today_ecuador = get_today_ecuador()
            cleaning_date = st.date_input(
                "Fecha de limpieza:",
                value=today_ecuador,
                max_value=today_ecuador,
                key="cleaning_date"
            )
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"], key="cleaning_type")
        with col2:
            available_students = [s.get('nombre', '') for s in st.session_state.students]
            st.write("Selecciona los estudiantes (1-3):")
            student1 = st.selectbox("Estudiante 1:", [""] + available_students, key="student1")
            student2 = st.selectbox("Estudiante 2 (opcional):", [""] + available_students, key="student2")
            student3 = st.selectbox("Estudiante 3 (opcional):", [""] + available_students, key="student3")
        submitted = st.form_submit_button("Registrar Limpieza")
        if submitted:
            students_selected = [s for s in [student1, student2, student3] if s and s.strip()]
            if not students_selected:
                st.error("❌ Debes seleccionar al menos un estudiante.")
            else:
                all_registered = all(student in available_students for student in students_selected)
                if not all_registered:
                    st.error("❌ Uno o más estudiantes no están registrados. Por favor regístralos primero.")
                else:
                    now_ecuador = get_now_ecuador()
                    new_record = {
                        'fecha': cleaning_date.strftime('%Y-%m-%d'),
                        'dia_semana': ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][cleaning_date.weekday()],
                        'hora': now_ecuador.strftime('%H:%M:%S'),
                        'estudiantes': students_selected,
                        'tipo_limpieza': cleaning_type,
                        'timestamp': now_ecuador.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.cleaning_history.append(new_record)
                    if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                        st.success("✅ Limpieza registrada exitosamente!")
                        st.balloons()
                        st.experimental_rerun()
                    else:
                        st.error("❌ Error al guardar el registro de limpieza.")

# Página de Reportes
elif page == "📊 Reportes":
    st.markdown('<h2 class="section-header">Historial y Reportes</h2>', unsafe_allow_html=True)
    today_ecuador = get_today_ecuador()
    week_ago = today_ecuador - timedelta(days=7)
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"], key="filter_type")
    with col2:
        date_range = st.date_input(
            "Rango de fechas:",
            value=(week_ago, today_ecuador),
            max_value=today_ecuador,
            key="date_range"
        )
    with col3:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

    filtered_history = st.session_state.cleaning_history.copy()
    if filter_type != "Todos":
        filtered_history = [r for r in filtered_history if r.get('tipo_limpieza') == filter_type]
    try:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered_history = [
                r for r in filtered_history 
                if start_date <= datetime.strptime(r.get('fecha','1970-01-01'), '%Y-%m-%d').date() <= end_date
            ]
    except Exception:
        pass

    if filtered_history:
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_cols = ['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']
        # Asegurar que columnas existan antes de mostrar
        display_cols = [c for c in display_cols if c in history_df.columns]
        display_df = history_df[display_cols]
        st.dataframe(display_df, use_container_width=True)

        st.subheader("Estadísticas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(filtered_history))
        col2.metric("Limpiezas de Aula", len([r for r in filtered_history if r.get('tipo_limpieza') == 'Aula']))
        col3.metric("Limpiezas de Baños", len([r for r in filtered_history if r.get('tipo_limpieza') == 'Baños']))

        st.subheader("Generar Reporte PDF")
        if not PDF_AVAILABLE:
            st.error("reportlab no está instalado. Ejecuta: pip install reportlab")
        else:
            if st.button("📥 Descargar Reporte Semanal"):
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history 
                                  if datetime.strptime(r.get('fecha','1970-01-01'), '%Y-%m-%d').date() in week_dates]
                    if week_records:
                        with st.spinner("Generando PDF..."):
                            pdf_path = generate_pdf_report(week_records, week_dates)
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            st.success("✅ PDF generado exitosamente!")
                            today_ecuador = get_today_ecuador()
                            st.download_button(
                                label="📄 Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_limpieza_semana_{today_ecuador.strftime('%Y-%m-%d')}.pdf",
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
st.markdown("---")
now_ecuador = get_now_ecuador()
st.markdown(
    f"""
    <div style='text-align:center; color:#666; font-size:0.9em;'>
        <p>Sistema de Registro de Limpieza 🧹</p>
        <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
        <p style='font-size:0.8em; color:#999;'>Hora de Ecuador: {now_ecuador.strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
    """,
    unsafe_allow_html=True
)
