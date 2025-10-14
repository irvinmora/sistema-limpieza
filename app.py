import streamlit as st
import json
import pandas as pd
from datetime import datetime, date, timedelta
import os
import base64
import pytz
import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

# SOLUCIÓN: Desactivar estadísticas para evitar errores de permisos
os.environ['STREAMLIT_GATHER_USAGE_STATS'] = 'false'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Configuración de zona horaria de Ecuador
ECUADOR_TZ = pytz.timezone('America/Guayaquil')

# CONFIGURACIÓN GOOGLE SHEETS
# Si no se configura, usará almacenamiento local
GOOGLE_CREDENTIALS = st.secrets.get("GOOGLE_CREDENTIALS", {}) if hasattr(st, 'secrets') else {}
GOOGLE_SHEET_URL = st.secrets.get("GOOGLE_SHEET_URL", "") if hasattr(st, 'secrets') else ""

# FUNCIÓN PARA OBTENER LA FECHA ACTUAL EN ECUADOR
def get_today_ecuador():
    """Retorna la fecha actual en zona horaria de Ecuador"""
    return datetime.now(ECUADOR_TZ).date()

def get_now_ecuador():
    """Retorna datetime actual en zona horaria de Ecuador"""
    return datetime.now(ECUADOR_TZ)

# SISTEMA DE ALMACENAMIENTO CON GOOGLE SHEETS
def get_google_sheets_client():
    """Conecta con Google Sheets usando las credenciales"""
    if not GOOGLE_CREDENTIALS:
        return None
    
    try:
        # Crear credenciales desde los secrets
        creds_dict = GOOGLE_CREDENTIALS
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Crear credenciales
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error conectando con Google Sheets: {e}")
        return None

def load_from_google_sheets():
    """Carga datos desde Google Sheets"""
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS:
        return None, None
    
    try:
        client = get_google_sheets_client()
        if not client:
            return None, None
        
        # Abrir la hoja de cálculo
        spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)
        
        # Cargar estudiantes
        try:
            students_sheet = spreadsheet.worksheet("Estudiantes")
            students_data = students_sheet.get_all_records()
            students = [s for s in students_data if s.get('nombre')]  # Filtrar filas vacías
        except:
            students = []
        
        # Cargar historial de limpieza
        try:
            history_sheet = spreadsheet.worksheet("Limpieza")
            history_data = history_sheet.get_all_records()
            # Convertir estudiantes de string a lista
            for record in history_data:
                if 'estudiantes' in record and isinstance(record['estudiantes'], str):
                    record['estudiantes'] = [s.strip() for s in record['estudiantes'].split(',')]
            cleaning_history = [h for h in history_data if h.get('fecha')]  # Filtrar filas vacías
        except:
            cleaning_history = []
        
        return students, cleaning_history
        
    except Exception as e:
        st.error(f"Error cargando desde Google Sheets: {e}")
        return None, None

def save_to_google_sheets(students, cleaning_history):
    """Guarda datos en Google Sheets"""
    if not GOOGLE_SHEET_URL or not GOOGLE_CREDENTIALS:
        return False
    
    try:
        client = get_google_sheets_client()
        if not client:
            return False
        
        spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)
        
        # Guardar estudiantes
        try:
            students_sheet = spreadsheet.worksheet("Estudiantes")
        except:
            # Crear hoja si no existe
            students_sheet = spreadsheet.add_worksheet(title="Estudiantes", rows="1000", cols="10")
            students_sheet.append_row(["id", "nombre", "fecha_registro", "fecha_actualizacion"])
        
        # Limpiar y actualizar datos de estudiantes
        students_sheet.clear()
        if students:
            # Preparar datos para Google Sheets
            students_df = pd.DataFrame(students)
            students_sheet.update([students_df.columns.values.tolist()] + students_df.values.tolist())
        
        # Guardar historial de limpieza
        try:
            history_sheet = spreadsheet.worksheet("Limpieza")
        except:
            # Crear hoja si no existe
            history_sheet = spreadsheet.add_worksheet(title="Limpieza", rows="1000", cols="10")
            history_sheet.append_row(["fecha", "dia_semana", "hora", "estudiantes", "tipo_limpieza", "timestamp"])
        
        # Preparar datos de limpieza para Google Sheets
        if cleaning_history:
            history_for_sheets = []
            for record in cleaning_history:
                # Convertir lista de estudiantes a string
                record_copy = record.copy()
                if 'estudiantes' in record_copy and isinstance(record_copy['estudiantes'], list):
                    record_copy['estudiantes'] = ', '.join(record_copy['estudiantes'])
                history_for_sheets.append(record_copy)
            
            history_df = pd.DataFrame(history_for_sheets)
            history_sheet.clear()
            history_sheet.update([history_df.columns.values.tolist()] + history_df.values.tolist())
        
        return True
        
    except Exception as e:
        st.error(f"Error guardando en Google Sheets: {e}")
        return False

# FUNCIONES MEJORADAS PARA MANEJO DE DATOS
def load_data(filename):
    """Carga datos con prioridad en Google Sheets"""
    # Primero intentar desde Google Sheets si está configurado
    if GOOGLE_SHEET_URL and GOOGLE_CREDENTIALS:
        students, cleaning_history = load_from_google_sheets()
        if students is not None and cleaning_history is not None:
            if filename == "students.json":
                return students
            elif filename == "cleaning_history.json":
                return cleaning_history
    
    # Fallback a almacenamiento local
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
    """Guarda datos tanto localmente como en Google Sheets"""
    success_local = False
    success_google = False
    
    # Guardar localmente
    try:
        os.makedirs("data", exist_ok=True)
        with open(f"data/{filename}", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        success_local = True
    except Exception as e:
        print(f"Error guardando localmente: {e}")
    
    # Guardar en Google Sheets si está configurado
    if GOOGLE_SHEET_URL and GOOGLE_CREDENTIALS:
        # Necesitamos ambos conjuntos de datos para guardar en Sheets
        if filename == "students.json":
            students = data
            cleaning_history = st.session_state.cleaning_history
        elif filename == "cleaning_history.json":
            students = st.session_state.students
            cleaning_history = data
        
        success_google = save_to_google_sheets(students, cleaning_history)
    
    return success_local or success_google

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
    PDF_AVAILABLE = False

# Estilos CSS personalizados y responsivos
st.markdown("""
<style>
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
    
    .info-message {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.5rem;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# FUNCIÓN MEJORADA PARA GENERAR PDF
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
        st.error(f"Error al generar PDF: {str(e)}")
        return None

def initialize_session_state():
    """Inicializa el estado de la sesión"""
    if 'students' not in st.session_state:
        st.session_state.students = load_data("students.json")
    if 'cleaning_history' not in st.session_state:
        st.session_state.cleaning_history = load_data("cleaning_history.json")
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = None
    if 'last_sync' not in st.session_state:
        st.session_state.last_sync = get_now_ecuador().strftime('%Y-%m-%d %H:%M:%S')

def get_current_week_dates():
    """Obtiene las fechas de la semana actual en zona horaria de Ecuador"""
    today = get_today_ecuador()
    start_of_week = today - timedelta(days=today.weekday())
    return [start_of_week + timedelta(days=i) for i in range(5)]

def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece"""
    updated_records = []
    for record in st.session_state.cleaning_history:
        updated_students = [s for s in record['estudiantes'] if s != student_name]
        if updated_students:
            record['estudiantes'] = updated_students
            updated_records.append(record)
    return updated_records

def update_cleaning_records_after_edit(old_name, new_name):
    """Actualiza el nombre del estudiante en todos los registros de limpieza"""
    for record in st.session_state.cleaning_history:
        if old_name in record['estudiantes']:
            record['estudiantes'] = [new_name if s == old_name else s for s in record['estudiantes']]

# INICIALIZAR ESTADO DE LA SESIÓN
initialize_session_state()

# Encabezado principal con fecha actual de Ecuador
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Mostrar fecha actual de Ecuador
today_ecuador = get_today_ecuador()
st.info(f"📅 Fecha actual: {today_ecuador.strftime('%d/%m/%Y')} - Hora de Ecuador")

# Información sobre el almacenamiento
if GOOGLE_SHEET_URL and GOOGLE_CREDENTIALS:
    st.success("📊 **Google Sheets activado** - Los datos se comparten entre todos los dispositivos")
    st.info(f"Última sincronización: {st.session_state.last_sync}")
else:
    st.warning("💾 **Almacenamiento local** - Los datos solo están en este dispositivo")
    st.markdown("""
    <div class="info-message">
    <strong>💡 Para habilitar sincronización entre dispositivos con Google Sheets:</strong><br>
    1. Crea una hoja de cálculo en Google Sheets<br>
    2. Compártela con acceso de edición para el servicio<br>
    3. Configura las credenciales en Hugging Face Secrets<br>
    4. Agrega la URL de la hoja de cálculo<br>
    <em>Configuración automática disponible en el botón de abajo</em>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón para configuración guiada
    if st.button("🛠️ Configurar Google Sheets"):
        st.markdown("""
        ### Configuración de Google Sheets
        
        **Paso 1:** Crear una hoja de cálculo en [Google Sheets](https://sheets.google.com)
        
        **Paso 2:** Compartir la hoja:
        - Haz clic en "Compartir"
        - Da acceso de **Editor** a la cuenta de servicio
        
        **Paso 3:** Obtener la URL de la hoja (ej: `https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit`)
        
        **Paso 4:** Configurar en Hugging Face Secrets:
        ```toml
        GOOGLE_SHEET_URL = "tu_url_de_google_sheets"
        GOOGLE_CREDENTIALS = { "type": "service_account", ... }
        ```
        """)

# Sidebar para navegación
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
    
    st.markdown("---")
    st.markdown("### 📊 Datos Actuales")
    st.markdown(f"**Estudiantes:** {len(st.session_state.students)}")
    st.markdown(f"**Registros:** {len(st.session_state.cleaning_history)}")
    
    # Botón para sincronizar con Google Sheets
    if GOOGLE_SHEET_URL and GOOGLE_CREDENTIALS:
        if st.button("🔄 Sincronizar con Google Sheets"):
            with st.spinner("Sincronizando..."):
                # Recargar datos desde Google Sheets
                new_students, new_history = load_from_google_sheets()
                
                if new_students is not None:
                    st.session_state.students = new_students
                if new_history is not None:
                    st.session_state.cleaning_history = new_history
                
                st.session_state.last_sync = get_now_ecuador().strftime('%Y-%m-%d %H:%M:%S')
                st.success("✅ Datos sincronizados correctamente")
                st.rerun()

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
        except:
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
                    value=st.session_state.editing_student['nombre'],
                    key="edit_student_name"
                )
            else:
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
                    old_name = st.session_state.editing_student['nombre']
                    old_id = st.session_state.editing_student['id']
                    
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s['nombre'] != old_name]
                    if student_name.upper() in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        now_ecuador = get_now_ecuador()
                        for student in st.session_state.students:
                            if student['nombre'] == old_name:
                                student['nombre'] = student_name
                                student['id'] = student_id.strip() if student_id else old_id
                                student['fecha_actualizacion'] = now_ecuador.strftime('%Y-%m-%d %H:%M:%S')
                                break
                        
                        update_cleaning_records_after_edit(old_name, student_name)
                        
                        if save_data(st.session_state.students, "students.json") and save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar los cambios.")
                else:
                    existing_students = [s['nombre'].upper() for s in st.session_state.students]
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
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar el estudiante.")
            else:
                st.error("❌ Por favor ingresa un nombre válido.")
    
    st.markdown('<h2 class="section-header">Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        st.dataframe(students_df[['nombre', 'id']], use_container_width=True)
        
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
            
            cleaning_count = 0
            if student_to_delete:
                cleaning_count = sum(1 for record in st.session_state.cleaning_history 
                                   if student_to_delete in record['estudiantes'])
                
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
                        st.session_state.students = [s for s in st.session_state.students 
                                                   if s['nombre'] != student_to_delete]
                        st.session_state.cleaning_history = update_cleaning_records_after_deletion(student_to_delete)
                        
                        if save_data(st.session_state.students, "students.json") and \
                           save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                            st.session_state.confirm_delete = None
                            st.success(f"✅ Estudiante '{student_to_delete}' eliminado exitosamente!")
                            if cleaning_count > 0:
                                st.success(f"✅ Removido de {cleaning_count} registro(s) de limpieza.")
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar el estudiante.")
                            st.session_state.confirm_delete = None
                
                with col_b:
                    if st.button("❌ Cancelar", key="confirm_no"):
                        st.session_state.confirm_delete = None
                        st.rerun()
            else:
                if st.button("🗑️ Eliminar Estudiante", type="secondary", key="delete_button"):
                    st.session_state.confirm_delete = student_to_delete
                    st.rerun()
    
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
                        st.rerun()
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
            st.error("reportlab no está instalado")
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