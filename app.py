import streamlit as st
import json
import pandas as pd
from datetime import datetime, date, timedelta
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
    initial_sidebar_state="expanded"
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
    try:
        import subprocess, sys
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

# Estilos CSS personalizados
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<style>
    .main-header {
        font-size: 3.5rem;
        color: red;
        text-align: center;
        margin-bottom: 3rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: blue;
        border-bottom: 5px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .success-message { padding: 1rem; background-color: #fce5cd; border: 10px solid #c3e6cb; border-radius: 1.5rem; color: #155724; }
    .warning-message { padding: 2rem; background-color: #fff3cd; border: 10px solid #ffeaa7; border-radius: 0.5rem; color: #856404; }
    .error-message { padding: 1rem; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 0.5rem; color: #721c24; }

    .custom-menu-btn {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 20px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        margin: 5px 0;
        transition: all 0.3s ease;
        width: 100%;
        text-align: center;
    }
    .custom-menu-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }

    .sidebar-content { padding: 10px; }

    /* Nota: la clase para ocultar el menú nativo puede variar entre versiones de Streamlit */
    .css-1d391kg {display: none;}
</style>
""", unsafe_allow_html=True)

# ------------------ Funciones de manejo de datos ------------------

def load_data(filename):
    """Carga JSON desde data/filename. Si no existe, lo crea y devuelve lista vacía."""
    try:
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            else:
                # Si no es lista, reescribir como lista vacía
                with open(filepath, "w", encoding="utf-8") as fw:
                    json.dump([], fw, ensure_ascii=False, indent=2)
                return []
    except json.JSONDecodeError:
        st.error(f"Error en el archivo {filename}. Se creará uno nuevo.")
        with open(os.path.join("data", filename), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    except Exception as e:
        st.error(f"Error al cargar {filename}: {e}")
        return []

def save_data(data, filename):
    """Guarda JSON de forma atómica en data/filename (escribe en temp y reemplaza)."""
    try:
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        os.replace(tmp_path, filepath)
        return True
    except Exception as e:
        st.error(f"Error al guardar {filename}: {e}")
        return False

def initialize_session_state():
    # Cargar datos al inicio
    if 'students' not in st.session_state:
        st.session_state.students = load_data("students.json")
    if 'cleaning_history' not in st.session_state:
        st.session_state.cleaning_history = load_data("cleaning_history.json")
    # Edición y navegación
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Inicio"
    # Estados para eliminación segura
    if 'pending_delete' not in st.session_state:
        st.session_state.pending_delete = None
    if 'show_confirm_delete' not in st.session_state:
        st.session_state.show_confirm_delete = False

def get_current_week_dates():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    return [start_of_week + timedelta(days=i) for i in range(5)]

# ------------------ PDF (igual que antes pero con defensas) ------------------

def generate_pdf_report(records, week_dates):
    try:
        if not PDF_AVAILABLE:
            raise ImportError("reportlab no está disponible")
        os.makedirs("reportes", exist_ok=True)
        pdf_path = f"reportes/reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30, alignment=TA_CENTER, textColor=colors.HexColor('#1f77b4'))
        title = Paragraph("REPORTE SEMANAL DE LIMPIEZA", title_style)
        story.append(title)

        week_info_style = ParagraphStyle('WeekInfo', parent=styles['Normal'], fontSize=12, spaceAfter=20, alignment=TA_CENTER)
        week_info = Paragraph(f"Semana del {week_dates[0].strftime('%d/%m/%Y')} al {week_dates[-1].strftime('%d/%m/%Y')}", week_info_style)
        story.append(week_info)
        story.append(Spacer(1, 20))

        if records:
            table_data = [['Fecha', 'Día', 'Estudiantes', 'Área', 'Hora']]
            for record in records:
                estudiantes = ', '.join(record.get('estudiantes', []))
                estudiantes = estudiantes.replace('•', '-').replace('–', '-').replace('—', '-')
                fecha_obj = datetime.strptime(record['fecha'], '%Y-%m-%d')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                table_data.append([fecha_formateada, record.get('dia_semana', ''), estudiantes, record.get('tipo_limpieza', ''), record.get('hora', '')])
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

            stats_style = ParagraphStyle('Stats', parent=styles['Normal'], fontSize=10, spaceAfter=6, leftIndent=20)
            total_registros = len(records)
            limpiezas_aula = len([r for r in records if r.get('tipo_limpieza') == 'Aula'])
            limpiezas_banos = len([r for r in records if r.get('tipo_limpieza') == 'Baños'])
            stats_text = f"<b>ESTADÍSTICAS:</b><br/>• Total de registros: {total_registros}<br/>• Limpiezas de aula: {limpiezas_aula}<br/>• Limpiezas de baños: {limpiezas_banos}<br/>"
            stats = Paragraph(stats_text, stats_style)
            story.append(stats)
        else:
            no_data_style = ParagraphStyle('NoData', parent=styles['Normal'], fontSize=12, textColor=colors.gray, alignment=TA_CENTER)
            no_data = Paragraph("No hay registros de limpieza para esta semana.", no_data_style)
            story.append(no_data)

        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        footer = Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Sistema de Registro de Limpieza", footer_style)
        story.append(footer)

        doc.build(story)
        return pdf_path
    except Exception as e:
        st.error(f"Error detallado al generar PDF: {str(e)}")
        return None

# ------------------ Actualización de registros al eliminar/editar ------------------

def update_cleaning_records_after_deletion(student_name, remove_empty_records=True):
    """
    Elimina al estudiante de todos los registros de limpieza donde aparece.
    Si remove_empty_records es True, también elimina registros que se quedan sin estudiantes.
    Retorna la lista de registros actualizada (para asignar a st.session_state.cleaning_history).
    """
    updated_records = []
    for record in st.session_state.cleaning_history:
        students_list = record.get('estudiantes', [])
        updated_students = [s for s in students_list if s != student_name]
        # asignar la lista actualizada al registro
        record['estudiantes'] = updated_students
        # mantener registro si queda estudiantes o si decidimos conservar registros vacíos
        if updated_students or not remove_empty_records:
            updated_records.append(record)
    return updated_records

def update_cleaning_records_after_edit(old_name, new_name):
    """Actualiza el nombre del estudiante en todos los registros de limpieza (in-place)."""
    for record in st.session_state.cleaning_history:
        if old_name in record.get('estudiantes', []):
            record['estudiantes'] = [new_name if s == old_name else s for s in record.get('estudiantes', [])]

# ------------------ Inicializar ------------------

initialize_session_state()

# ------------------ Sidebar / navegación ------------------

with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown("## 🧭 Menú de Navegación")
    st.markdown("---")

    if st.button("🏠 **INICIO**", use_container_width=True, type="primary" if st.session_state.page == "🏠 Inicio" else "secondary"):
        st.session_state.page = "🏠 Inicio"
        st.rerun()
    if st.button("👥 **REGISTRO DE ESTUDIANTES**", use_container_width=True, type="primary" if st.session_state.page == "👥 Registro de Estudiantes" else "secondary"):
        st.session_state.page = "👥 Registro de Estudiantes"
        st.rerun()
    if st.button("📝 **REGISTRO DE LIMPIEZA**", use_container_width=True, type="primary" if st.session_state.page == "📝 Registro de Limpieza" else "secondary"):
        st.session_state.page = "📝 Registro de Limpieza"
        st.rerun()
    if st.button("📊 **HISTORIAL DE LIMPIEZA**", use_container_width=True, type="primary" if st.session_state.page == "📊 Historial de Limpieza" else "secondary"):
        st.session_state.page = "📊 Historial de Limpieza"
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Estadísticas Rápidas")
    st.metric("Estudiantes", len(st.session_state.students))
    st.metric("Registros", len(st.session_state.cleaning_history))
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ Contenido principal ------------------

st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)
page = st.session_state.page

# ---------- Página Inicio ----------
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Bienvenido al Sistema de Registro de Limpieza</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Estudiantes", len(st.session_state.students))
    col2.metric("Registros de Limpieza", len(st.session_state.cleaning_history))

    try:
        week_dates = get_current_week_dates()
        week_records = [r for r in st.session_state.cleaning_history if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
    except Exception:
        week_records = []
    col3.metric("Limpiezas Esta Semana", len(week_records))

    st.subheader("📅 Resumen de Limpiezas - Semana Actual")
    try:
        week_summary = []
        for day_date in week_dates:
            day_name = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][day_date.weekday()]
            day_records = [r for r in st.session_state.cleaning_history if datetime.strptime(r['fecha'], '%Y-%m-%d').date() == day_date]
            for record in day_records:
                week_summary.append({
                    'Día': day_name,
                    'Fecha': day_date.strftime('%d/%m/%Y'),
                    'Estudiantes': ', '.join(record.get('estudiantes', [])),
                    'Área': record.get('tipo_limpieza', ''),
                    'Hora': record.get('hora', '')
                })
        if week_summary:
            df_week = pd.DataFrame(week_summary)
            st.dataframe(df_week, use_container_width=True)
        else:
            st.info("No hay registros de limpieza para esta semana.")
    except Exception as e:
        st.error(f"Error al cargar el resumen semanal: {e}")

# ---------- Página Registro de Estudiantes ----------
elif page == "👥 Registro de Estudiantes":
    st.markdown('<h2 class="section-header">👥 Gestión de Estudiantes</h2>', unsafe_allow_html=True)

    # Formulario agregar/editar
    with st.form("student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_name = st.text_input("Nombre completo del estudiante:", value=st.session_state.editing_student['nombre'], key="edit_student_name")
            else:
                student_name = st.text_input("Nombre completo del estudiante:", key="student_name")
        with col2:
            if st.session_state.edit_mode and st.session_state.editing_student:
                student_id = st.text_input("ID o Matrícula:", value=st.session_state.editing_student.get('id', ''), key="edit_student_id")
            else:
                student_id = st.text_input("ID o Matrícula (opcional):", key="student_id")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Guardar Cambios" if st.session_state.edit_mode else "👤 Agregar Estudiante")
        with col2:
            if st.session_state.edit_mode:
                if st.form_submit_button("❌ Cancelar Edición"):
                    st.session_state.edit_mode = False
                    st.session_state.editing_student = None
                    st.rerun()

        if submitted:
            if student_name.strip():
                student_name_clean = student_name.strip().upper()
                if st.session_state.edit_mode and st.session_state.editing_student:
                    old_name = st.session_state.editing_student['nombre']
                    old_id = st.session_state.editing_student.get('id', '')
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s['nombre'] != old_name]
                    if student_name_clean in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        for student in st.session_state.students:
                            if student['nombre'] == old_name:
                                student['nombre'] = student_name_clean
                                student['id'] = student_id.strip() if student_id else old_id
                                student['fecha_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                break
                        # actualizar registros y guardar
                        update_cleaning_records_after_edit(old_name, student_name_clean)
                        ok1 = save_data(st.session_state.students, "students.json")
                        ok2 = save_data(st.session_state.cleaning_history, "cleaning_history.json")
                        if ok1 and ok2:
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar los cambios.")
                else:
                    existing_students = [s['nombre'].upper() for s in st.session_state.students]
                    if student_name_clean in existing_students:
                        st.error("❌ Este estudiante ya está registrado.")
                    else:
                        new_student = {
                            'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                            'nombre': student_name_clean,
                            'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.students.append(new_student)
                        if save_data(st.session_state.students, "students.json"):
                            st.success("✅ Estudiante registrado exitosamente!")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar el estudiante.")
            else:
                st.error("❌ Por favor ingresa un nombre válido.")

    # Lista estudiantes
    st.markdown('<h2 class="section-header">📋 Lista de Estudiantes</h2>', unsafe_allow_html=True)
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        display_df = students_df[['nombre', 'id']].copy()
        display_df['Acciones'] = "Editar | Eliminar"
        st.dataframe(display_df, use_container_width=True)

        st.markdown("### 🔧 Gestión de Estudiantes")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✏️ Editar Estudiante")
            student_to_edit = st.selectbox("Selecciona un estudiante para editar:", [s['nombre'] for s in st.session_state.students], key="edit_select")
            if st.button("📝 Editar Estudiante", key="edit_button"):
                student = next((s for s in st.session_state.students if s['nombre'] == student_to_edit), None)
                if student:
                    st.session_state.editing_student = student
                    st.session_state.edit_mode = True
                    st.rerun()
        with col2:
            st.subheader("🗑️ Eliminar Estudiante")
            student_to_delete = st.selectbox("Selecciona un estudiante para eliminar:", [s['nombre'] for s in st.session_state.students], key="delete_select")

            # Conteo de apariciones
            cleaning_count = sum(1 for record in st.session_state.cleaning_history if student_to_delete in record.get('estudiantes', []))

            if cleaning_count > 0:
                st.warning(f"⚠️ **Advertencia:** Este estudiante aparece en **{cleaning_count}** registros de limpieza.")
                st.info("💡 **Nota:** Al confirmar, se eliminará el estudiante de todos esos registros.")

            # iniciar eliminación (abrir panel confirm)
            if st.button("❌ Eliminar Estudiante", key="delete_button"):
                st.session_state.pending_delete = student_to_delete
                st.session_state.show_confirm_delete = True
                st.rerun()

            # Panel de confirmación
            if st.session_state.show_confirm_delete and st.session_state.pending_delete == student_to_delete:
                st.error("🚨 **¡ADVERTENCIA!** Esta acción quitará al estudiante de todos los registros donde aparece.")
                option = st.radio("¿Qué hacer con los registros que queden sin estudiantes?", ("Eliminar registros vacíos", "Conservar registros (dejar campo vacío)"), index=0)

                if st.button("✅ Confirmar eliminación"):
                    # Eliminar estudiante de la lista principal
                    st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]

                    # Actualizar historial (obtener lista nueva)
                    new_history = update_cleaning_records_after_deletion(student_to_delete, remove_empty_records=(option == "Eliminar registros vacíos"))
                    st.session_state.cleaning_history = new_history

                    # Guardar ambos archivos
                    saved_students = save_data(st.session_state.students, "students.json")
                    saved_history = save_data(st.session_state.cleaning_history, "cleaning_history.json")

                    # Limpiar estado
                    st.session_state.pending_delete = None
                    st.session_state.show_confirm_delete = False

                    if saved_students and saved_history:
                        st.success("✅ Estudiante eliminado y registros actualizados exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar los cambios. Verifique permisos de escritura en la carpeta 'data'.")

    else:
        st.info("📝 No hay estudiantes registrados aún.")

# ---------- Página Registro de Limpieza ----------
elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 class="section-header">📝 Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)

    with st.form("cleaning_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today(), key="cleaning_date")
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"], key="cleaning_type")
        with col2:
            available_students = [s['nombre'] for s in st.session_state.students]
            if not available_students:
                st.error("❌ No hay estudiantes registrados. Por favor registra estudiantes primero.")
            else:
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
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar el registro de limpieza.")

# ---------- Página Historial de Limpieza ----------
elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 class="section-header">📊 Historial de Limpieza</h2>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"], key="filter_type")
    with col2:
        date_range = st.date_input(
            "Rango de fechas:",
            value=(date.today() - timedelta(days=7), date.today()),
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
        filtered_history = [r for r in filtered_history if r.get('tipo_limpieza') == filter_type]
    try:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered_history = [
                r for r in filtered_history
                if start_date <= datetime.strptime(r['fecha'], '%Y-%m-%d').date() <= end_date
            ]
    except Exception:
        pass

    if filtered_history:
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        st.dataframe(display_df, use_container_width=True)

        st.subheader("📈 Estadísticas")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(filtered_history))
        col2.metric("Limpiezas de Aula", len([r for r in filtered_history if r.get('tipo_limpieza') == 'Aula']))
        col3.metric("Limpiezas de Baños", len([r for r in filtered_history if r.get('tipo_limpieza') == 'Baños']))

        st.subheader("📄 Generar Reporte PDF")
        if not PDF_AVAILABLE:
            st.error("""**reportlab no está instalado. Para generar PDFs, ejecuta:**
```bash
pip install reportlab
```""")
        else:
            if st.button("📥 Descargar Reporte Semanal en PDF"):
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
                    if week_records:
                        with st.spinner("Generando PDF..."):
                            pdf_path = generate_pdf_report(week_records, week_dates)
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            st.success("✅ PDF generado exitosamente!")
                            st.download_button(label="📄 Descargar PDF", data=pdf_data, file_name=f"reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf", mime="application/pdf", key="download_pdf")
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
st.markdown("""
    <div style='text-align:center; color:#666; font-size:0.9em;'>
        <p>Sistema de Registro de Limpieza 🧹</p>
        <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
    </div>
""", unsafe_allow_html=True)
