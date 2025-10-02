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
    initial_sidebar_state="collapsed"  # Menú hamburguesa por defecto en móviles
)

# Estilos CSS modernos y responsivos
st.markdown("""
<style>
    /* Fondo gradiente moderno */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        min-height: 100vh;
    }
    
    /* Contenedor principal con glassmorphism */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Header principal */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
    }
    
    /* Headers de sección */
    .section-header {
        font-size: 1.8rem;
        color: #4a5568;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
        font-weight: 600;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
        text-align: center;
        margin: 0.5rem;
    }
    
    /* Botones modernos */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Formularios */
    .stForm {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .sidebar .sidebar-content {
        background: transparent !important;
    }
    
    /* Mensajes de estado */
    .success-message {
        background: linear-gradient(135deg, #48bb78, #38a169);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: none;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #ed8936, #dd6b20);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: none;
    }
    
    .error-message {
        background: linear-gradient(135deg, #f56565, #e53e3e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: none;
    }
    
    /* Dataframes */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* Responsive design para móviles */
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
        
        .stForm {
            padding: 1rem;
        }
    }
    
    /* Mejoras para elementos de streamlit */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stDateInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# IMPORTACIÓN SEGURA DEL PDF GENERATOR CON CODIFICACIÓN CORREGIDA
try:
    from utils.pdf_generator import generate_pdf_report
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    st.error(f"Error al cargar el generador de PDF: {e}")

# FUNCIONES PARA MANEJO DE DATOS (MISMA LÓGICA ORIGINAL)
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
    # Estado para limpiar formularios
    if 'form_cleared' not in st.session_state:
        st.session_state.form_cleared = False

def get_current_week_dates():
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    return [start_of_week + pd.Timedelta(days=i) for i in range(5)]

initialize_session_state()

# Sidebar para navegación (menú hamburguesa)
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; 
                border-radius: 15px; 
                color: white; 
                text-align: center;
                margin-bottom: 2rem;'>
        <h1>🧹</h1>
        <h3>Sistema de Limpieza</h3>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "**Navegación**", 
        ["🏠 Inicio", "👥 Registro de Estudiantes", "📝 Registro de Limpieza", "📊 Historial de Limpieza"],
        key="navigation"
    )

# Contenedor principal
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Bienvenido al Sistema de Registro de Limpieza</h2>', unsafe_allow_html=True)
    
    # Métricas en tarjetas modernas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Estudiantes</h3>
            <h2 style='color: #667eea; font-size: 2.5rem; margin: 0;'>{len(st.session_state.students)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📝 Registros Totales</h3>
            <h2 style='color: #667eea; font-size: 2.5rem; margin: 0;'>{len(st.session_state.cleaning_history)}</h2>
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
            <h2 style='color: #667eea; font-size: 2.5rem; margin: 0;'>{len(week_records)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen de limpiezas de la semana actual
    st.markdown('<h2 class="section-header">📅 Resumen de Limpiezas - Semana Actual</h2>', unsafe_allow_html=True)
    
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
    with st.form("student_form", clear_on_submit=True):  # CLEAR_ON_SUBMIT SOLUCIONA EL PROBLEMA
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("Nombre completo del estudiante:", key="student_name")
        with col2:
            student_id = st.text_input("ID o Matrícula (opcional):", key="student_id")
        
        submitted = st.form_submit_button("🎓 Agregar Estudiante")
        
        if submitted:
            if student_name.strip():
                student_name = student_name.strip().upper()
                existing_students = [s['nombre'].upper() for s in st.session_state.students]
                if student_name.upper() in existing_students:
                    st.markdown('<div class="warning-message">⚠️ Este estudiante ya está registrado.</div>', unsafe_allow_html=True)
                else:
                    new_student = {
                        'id': student_id.strip() if student_id else f"ST{len(st.session_state.students) + 1:03d}",
                        'nombre': student_name,
                        'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.students.append(new_student)
                    if save_data(st.session_state.students, "students.json"):
                        st.markdown('<div class="success-message">✅ Estudiante registrado exitosamente!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-message">❌ Error al guardar el estudiante.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-message">❌ Por favor ingresa un nombre válido.</div>', unsafe_allow_html=True)
    
    # Lista de estudiantes registrados
    st.markdown('<h2 class="section-header">📋 Lista de Estudiantes Registrados</h2>', unsafe_allow_html=True)
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        st.dataframe(students_df[['nombre', 'id']], use_container_width=True)
        
        # Opciones de eliminación
        with st.expander("🗑️ Opciones de Eliminación"):
            student_to_delete = st.selectbox(
                "Selecciona un estudiante para eliminar:",
                [s['nombre'] for s in st.session_state.students],
                key="delete_student"
            )
            if st.button("Eliminar Estudiante", type="secondary"):
                st.session_state.students = [s for s in st.session_state.students if s['nombre'] != student_to_delete]
                if save_data(st.session_state.students, "students.json"):
                    st.markdown('<div class="success-message">✅ Estudiante eliminado exitosamente!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown('<div class="error-message">❌ Error al eliminar el estudiante.</div>', unsafe_allow_html=True)
    else:
        st.info("📝 No hay estudiantes registrados aún.")

# Página de Registro de Limpieza
elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 class="section-header">📝 Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    
    with st.form("cleaning_form", clear_on_submit=True):  # CLEAR_ON_SUBMIT SOLUCIONA EL PROBLEMA
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
        
        submitted = st.form_submit_button("💾 Registrar Limpieza")
        
        if submitted:
            students_selected = [s for s in [student1, student2, student3] if s.strip()]
            if not students_selected:
                st.markdown('<div class="error-message">❌ Debes seleccionar al menos un estudiante.</div>', unsafe_allow_html=True)
            else:
                all_registered = all(student in available_students for student in students_selected)
                if not all_registered:
                    st.markdown('<div class="error-message">❌ Uno o más estudiantes no están registrados. Por favor regístralos primero.</div>', unsafe_allow_html=True)
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
                        st.markdown('<div class="success-message">✅ Limpieza registrada exitosamente!</div>', unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.markdown('<div class="error-message">❌ Error al guardar el registro de limpieza.</div>', unsafe_allow_html=True)

# Página de Historial de Limpieza
elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 class="section-header">📊 Historial de Limpieza</h2>', unsafe_allow_html=True)
    
    # Filtros
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

    # Filtrar historial
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
        # Mostrar historial
        history_df = pd.DataFrame(filtered_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        st.dataframe(display_df, use_container_width=True)

        # Estadísticas
        st.markdown('<h2 class="section-header">📈 Estadísticas</h2>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(filtered_history))
        col2.metric("Limpiezas de Aula", len([r for r in filtered_history if r['tipo_limpieza'] == 'Aula']))
        col3.metric("Limpiezas de Baños", len([r for r in filtered_history if r['tipo_limpieza'] == 'Baños']))

        # Generar PDF
        st.markdown('<h2 class="section-header">📄 Generar Reporte PDF</h2>', unsafe_allow_html=True)
        
        if not PDF_AVAILABLE:
            st.markdown('<div class="warning-message">⚠️ El generador de PDF no está disponible. Verifica que el archivo utils/pdf_generator.py exista.</div>', unsafe_allow_html=True)
        
        if st.button("📥 Descargar Reporte Semanal en PDF"):
            if PDF_AVAILABLE:
                try:
                    week_dates = get_current_week_dates()
                    week_records = [r for r in st.session_state.cleaning_history 
                                  if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
                    if week_records:
                        pdf_path = generate_pdf_report(week_records, week_dates)
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                            st.download_button(
                                label="📄 Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_limpieza_semana_{date.today().strftime('%Y-%m-%d')}.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.error("No se pudo generar el archivo PDF.")
                    else:
                        st.info("No hay registros de limpieza para esta semana.")
                except Exception as e:
                    st.error(f"Error al generar el PDF: {str(e)}")
            else:
                st.error("El generador de PDF no está disponible.")
    else:
        st.info("No hay registros de limpieza que coincidan con los filtros seleccionados.")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style='text-align:center; color:white; font-size:0.9em; padding:2rem;'>
    <p>Sistema de Registro de Limpieza 🧹</p>
    <p>© 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</p>
</div>
""", unsafe_allow_html=True)