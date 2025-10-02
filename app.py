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

# Estilos CSS personalizados + RESPONSIVE
st.markdown("""
<style>
    /* Estilo general */
    .main-header {
        font-size: 2.2rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
    }
    /* Mensajes personalizados */
    .success-message, .warning-message {
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    /* Dataframes scrollables */
    .scroll-table {
        overflow-x: auto;
    }
    /* Estilos responsivos para pantallas pequeñas */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.6rem;
        }
        .section-header {
            font-size: 1.2rem;
        }
        .stButton button, .stDownloadButton button {
            width: 100% !important;
        }
        .stTextInput, .stSelectbox, .stDateInput {
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# IMPORTACIÓN SEGURA DEL PDF GENERATOR
try:
    from utils.pdf_generator import generate_pdf_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    def generate_pdf_report(records, week_dates):
        st.error("PDF generator not available")
        return None

# FUNCIONES CORREGIDAS PARA MANEJO DE DATOS
def load_data(filename):
    try:
        filepath = f"data/{filename}"
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception:
        return []

def save_data(data, filename):
    try:
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def initialize_session_state():
    if 'students' not in st.session_state:
        students_data = load_data("students.json")
        st.session_state.students = students_data if isinstance(students_data, list) else []
    if 'cleaning_history' not in st.session_state:
        history_data = load_data("cleaning_history.json")
        st.session_state.cleaning_history = history_data if isinstance(history_data, list) else []

def get_current_week_dates():
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    week_dates = [start_of_week + pd.Timedelta(days=i) for i in range(5)]
    return week_dates

# Inicializar datos
initialize_session_state()

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una sección:", 
                       ["🏠 Inicio", "👥 Registro de Estudiantes", "📝 Registro de Limpieza", "📊 Historial de Limpieza"])

# ---------------- PÁGINAS ---------------- #
# Página de Inicio
if page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Bienvenido</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.metric("Total Estudiantes", len(st.session_state.students))
    with col2:
        st.metric("Registros de Limpieza", len(st.session_state.cleaning_history))
    with col3:
        try:
            week_dates = get_current_week_dates()
            week_records = [r for r in st.session_state.cleaning_history 
                           if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
        except:
            week_records = []
        st.metric("Limpiezas Semana", len(week_records))

    st.subheader("📅 Resumen Semana Actual")
    try:
        week_dates = get_current_week_dates()
        week_summary = []
        for day_date in week_dates:
            day_name = ["Lunes","Martes","Miércoles","Jueves","Viernes"][day_date.weekday()]
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
            st.markdown('<div class="scroll-table">', unsafe_allow_html=True)
            st.dataframe(df_week, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No hay registros de esta semana.")
    except Exception as e:
        st.error(f"Error al cargar resumen: {e}")

# Página de Registro de Estudiantes
elif page == "👥 Registro de Estudiantes":
    st.markdown('<h2 class="section-header">Registro de Estudiantes</h2>', unsafe_allow_html=True)
    with st.form("student_form"):
        student_name = st.text_input("Nombre completo:")
        student_id = st.text_input("ID o Matrícula (opcional):")
        submitted = st.form_submit_button("Agregar Estudiante")
        if submitted:
            if student_name.strip():
                existing = [s['nombre'].lower() for s in st.session_state.students]
                if student_name.lower() in existing:
                    st.warning("⚠️ Estudiante ya registrado.")
                else:
                    new_student = {
                        'id': student_id.strip() if student_id else f"ST{len(st.session_state.students)+1:03d}",
                        'nombre': student_name.strip(),
                        'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.students.append(new_student)
                    if save_data(st.session_state.students, "students.json"):
                        st.success("✅ Registrado!")
                    else:
                        st.error("❌ Error al guardar.")
            else:
                st.error("❌ Ingresa un nombre válido.")
    st.subheader("Lista de Estudiantes")
    if st.session_state.students:
        df = pd.DataFrame(st.session_state.students)
        st.markdown('<div class="scroll-table">', unsafe_allow_html=True)
        st.dataframe(df[['nombre','id']], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Sin estudiantes registrados.")

# Página de Registro de Limpieza
elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 class="section-header">Registro de Limpieza</h2>', unsafe_allow_html=True)
    with st.form("cleaning_form"):
        cleaning_date = st.date_input("Fecha:", value=date.today())
        cleaning_type = st.selectbox("Tipo:", ["Aula", "Baños"])
        available_students = [s['nombre'] for s in st.session_state.students]
        student1 = st.selectbox("Estudiante 1:", [""]+available_students)
        student2 = st.selectbox("Estudiante 2:", [""]+available_students)
        student3 = st.selectbox("Estudiante 3:", [""]+available_students)
        submitted = st.form_submit_button("Registrar Limpieza")
        if submitted:
            students_selected = [s for s in [student1,student2,student3] if s.strip()]
            if not students_selected:
                st.error("❌ Selecciona al menos un estudiante.")
            else:
                new_record = {
                    'fecha': cleaning_date.strftime('%Y-%m-%d'),
                    'dia_semana': ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][cleaning_date.weekday()],
                    'hora': datetime.now().strftime('%H:%M:%S'),
                    'estudiantes': students_selected,
                    'tipo_limpieza': cleaning_type,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.session_state.cleaning_history.append(new_record)
                if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                    st.success("✅ Limpieza registrada!")
                    st.balloons()
                else:
                    st.error("❌ Error al guardar.")

# Página de Historial
elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 class="section-header">Historial de Limpieza</h2>', unsafe_allow_html=True)
    filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "Aula", "Baños"])
    date_range = st.date_input("Rango de fechas:", value=(date.today()-pd.Timedelta(days=7), date.today()))
    if isinstance(date_range, tuple) and len(date_range)==2:
        start_date, end_date = date_range
    else:
        start_date=end_date=date_range
    filtered = st.session_state.cleaning_history
    if filter_type!="Todos":
        filtered=[r for r in filtered if r['tipo_limpieza']==filter_type]
    filtered=[r for r in filtered if start_date <= datetime.strptime(r['fecha'],'%Y-%m-%d').date() <= end_date]
    if filtered:
        df=pd.DataFrame(filtered)
        df['Fecha']=pd.to_datetime(df['fecha']).dt.strftime('%d/%m/%Y')
        display_df=df[['Fecha','dia_semana','hora','estudiantes','tipo_limpieza']]
        st.markdown('<div class="scroll-table">', unsafe_allow_html=True)
        st.dataframe(display_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay registros con los filtros seleccionados.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;'>Sistema de Registro de Limpieza 🧹</div>", unsafe_allow_html=True)
