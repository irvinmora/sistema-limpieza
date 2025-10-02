import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import os

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
</style>
""", unsafe_allow_html=True)

# IMPORTACIÓN SEGURA DEL PDF GENERATOR
try:
    from utils.pdf_generator import generate_pdf_report
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    # Función dummy como fallback
    def generate_pdf_report(records, week_dates):
        st.error("PDF generator not available")
        return None

# FUNCIONES CORREGIDAS PARA MANEJO DE DATOS
def load_data(filename):
    """Cargar datos desde archivo JSON con manejo de errores"""
    try:
        filepath = f"data/{filename}"
        # Verificar si el archivo existe y no está vacío
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            # Si el archivo no existe o está vacío, retornar lista vacía
            return []
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # Si el archivo está vacío
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []
    except Exception as e:
        return []

def save_data(data, filename):
    """Guardar datos en archivo JSON con manejo de errores"""
    try:
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

def initialize_session_state():
    """Inicializar el estado de la sesión"""
    if 'students' not in st.session_state:
        students_data = load_data("students.json")
        # Asegurarse de que sea una lista
        st.session_state.students = students_data if isinstance(students_data, list) else []
    
    if 'cleaning_history' not in st.session_state:
        history_data = load_data("cleaning_history.json")
        # Asegurarse de que sea una lista
        st.session_state.cleaning_history = history_data if isinstance(history_data, list) else []

def get_current_week_dates():
    """Obtener las fechas de la semana actual (lunes a viernes)"""
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    week_dates = [start_of_week + pd.Timedelta(days=i) for i in range(5)]  # Lunes a Viernes
    return week_dates

# Inicializar datos
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
    
    with col1:
        st.metric("Total Estudiantes", len(st.session_state.students))
    
    with col2:
        st.metric("Registros de Limpieza", len(st.session_state.cleaning_history))
    
    with col3:
        week_records = []
        try:
            week_dates = get_current_week_dates()
            week_records = [r for r in st.session_state.cleaning_history 
                           if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
        except:
            week_records = []
        st.metric("Limpiezas Esta Semana", len(week_records))
    
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
    st.markdown('<h2 class="section-header">👥 Registro de Estudiantes</h2>', unsafe_allow_html=True)
    
    # Formulario para agregar estudiantes
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            student_name = st.text_input("Nombre completo del estudiante:")
        
        with col2:
            student_id = st.text_input("ID o Matrícula (opcional):")
        
        submitted = st.form_submit_button("Agregar Estudiante")
        
        if submitted:
            if student_name.strip():
                # Verificar si el estudiante ya existe
                existing_students = [s['nombre'].lower() for s in st.session_state.students]
                if student_name.lower() in existing_students:
                    st.warning("⚠️ Este estudiante ya está registrado.")
                else:
                    new_student = {
                        'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                        'nombre': student_name.strip(),
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
    st.subheader("Lista de Estudiantes Registrados")
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        st.dataframe(students_df[['nombre', 'id']], use_container_width=True)
        
        # Opción para eliminar estudiantes
        if st.checkbox("Mostrar opciones de eliminación"):
            student_to_delete = st.selectbox(
                "Selecciona un estudiante para eliminar:",
                [s['nombre'] for s in st.session_state.students]
            )
            if st.button("Eliminar Estudiante"):
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
    
    with st.form("cleaning_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today())
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"])
        
        with col2:
            # Selección de estudiantes
            available_students = [s['nombre'] for s in st.session_state.students]
            
            st.write("Selecciona los estudiantes (1-3):")
            student1 = st.selectbox("Estudiante 1:", [""] + available_students)
            student2 = st.selectbox("Estudiante 2 (opcional):", [""] + available_students)
            student3 = st.selectbox("Estudiante 3 (opcional):", [""] + available_students)
        
        submitted = st.form_submit_button("Registrar Limpieza")
        
        if submitted:
            # Validar que al menos un estudiante sea seleccionado
            students_selected = [s for s in [student1, student2, student3] if s.strip()]
            
            if not students_selected:
                st.error("❌ Debes seleccionar al menos un estudiante.")
            else:
                # Verificar que todos los estudiantes estén registrados
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
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"])
    
    with col2:
        date_range = st.date_input(
            "Rango de fechas:",
            value=(date.today() - pd.Timedelta(days=7), date.today()),
            max_value=date.today()
        )
    
    with col3:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range
    
    # Aplicar filtros
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
    
    # Mostrar historial
    if filtered_history:
        # Convertir a DataFrame para mejor visualización
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Estadísticas
        st.subheader("📈 Estadísticas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_records = len(filtered_history)
            st.metric("Total Registros", total_records)
        
        with col2:
            aula_count = len([r for r in filtered_history if r['tipo_limpieza'] == 'Aula'])
            st.metric("Limpiezas de Aula", aula_count)
        
        with col3:
            banos_count = len([r for r in filtered_history if r['tipo_limpieza'] == 'Baños'])
            st.metric("Limpiezas de Baños", banos_count)
        
        # Generar reporte PDF (solo si está disponible)
        st.subheader("📄 Generar Reporte PDF")
        if not PDF_AVAILABLE:
            st.warning("⚠️ El generador de PDF no está disponible. Verifica que el archivo utils/pdf_generator.py exista.")
        
        if st.button("Descargar Reporte Semanal en PDF"):
            if PDF_AVAILABLE:
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history 
                                  if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
                    
                    if week_records:
                        pdf_path = generate_pdf_report(week_records, week_dates)
                        if pdf_path:
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            
                            st.download_button(
                                label="Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.warning("No hay registros de limpieza para esta semana.")
                except Exception as e:
                    st.error(f"Error al generar el PDF: {e}")
            else:
                st.error("El generador de PDF no está disponible.")
    
    else:
        st.info("No hay registros de limpieza que coincidan con los filtros seleccionados.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:#666; font-size:0.9em;'>
        <p>Sistema de Registro de Limpieza 🧹</p>
        <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
    </div>
    """,
    unsafe_allow_html=True
)