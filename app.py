import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import os

# Configuración inicial
os.environ['STREAMLIT_GATHER_USAGE_STATS'] = 'false'
st.set_page_config(
    page_title="Sistema de Registro de Limpieza",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS moderno y responsivo
st.markdown("""
<style>
    /* Tipografía y color general */
    body { font-family: 'Arial', sans-serif; color: #333; }
    h1, h2, h3 { color: #1f77b4; }
    
    /* Encabezado principal */
    .main-header { font-size: 2rem; text-align: center; margin-bottom: 1rem; }
    
    /* Cards para métricas */
    .metric-card {
        padding: 1rem; margin: 0.5rem; border-radius: 0.8rem;
        background-color: #f8f9fa; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Tablas responsivas */
    .dataframe { width: 100% !important; overflow-x: auto; }
    
    /* Footer */
    .footer { text-align: center; color: #666; font-size: 0.8em; margin-top: 2rem; padding: 1rem 0; }
    
    /* Formularios y botones */
    input, select, textarea { width: 100% !important; }
    
    @media (max-width: 768px) {
        .main-header { font-size: 1.5rem; }
        .metric-card { margin: 0.3rem 0; }
    }
</style>
""", unsafe_allow_html=True)

# Funciones para manejo de datos
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

def get_current_week_dates():
    today = date.today()
    start_of_week = today - pd.Timedelta(days=today.weekday())
    return [start_of_week + pd.Timedelta(days=i) for i in range(5)]

initialize_session_state()

# Sidebar tipo hamburguesa
with st.sidebar:
    st.title("Navegación")
    page = st.radio("Ir a:", ["🏠 Inicio", "👥 Estudiantes", "📝 Limpieza", "📊 Historial"])

# Encabezado
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# --- PÁGINAS ---
if page == "🏠 Inicio":
    st.subheader("📊 Resumen")
    col1, col2, col3 = st.columns(3)
    
    col1.markdown(f'<div class="metric-card"><h3>{len(st.session_state.students)}</h3><p>Estudiantes</p></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><h3>{len(st.session_state.cleaning_history)}</h3><p>Registros</p></div>', unsafe_allow_html=True)
    
    week_dates = get_current_week_dates()
    week_records = [r for r in st.session_state.cleaning_history if datetime.strptime(r['fecha'], '%Y-%m-%d').date() in week_dates]
    col3.markdown(f'<div class="metric-card"><h3>{len(week_records)}</h3><p>Limpiezas Semana</p></div>', unsafe_allow_html=True)
    
    # Tabla resumida de la semana
    if week_records:
        summary = []
        for r in week_records:
            summary.append({
                "Fecha": r['fecha'],
                "Día": r['dia_semana'],
                "Estudiantes": ', '.join(r['estudiantes']),
                "Área": r['tipo_limpieza'],
                "Hora": r['hora']
            })
        st.dataframe(pd.DataFrame(summary), use_container_width=True)
    else:
        st.info("No hay registros esta semana.")

elif page == "👥 Estudiantes":
    st.subheader("👥 Registro de Estudiantes")
    with st.form("form_student"):
        name = st.text_input("Nombre completo:")
        student_id = st.text_input("ID (opcional):")
        submitted = st.form_submit_button("Agregar")
        if submitted:
            if not name.strip():
                st.error("Ingrese un nombre válido")
            elif name.lower() in [s['nombre'].lower() for s in st.session_state.students]:
                st.warning("Estudiante ya registrado")
            else:
                new_student = {'id': student_id or f"ST{len(st.session_state.students)+1:03d}",
                               'nombre': name.strip(),
                               'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                st.session_state.students.append(new_student)
                save_data(st.session_state.students, "students.json")
                st.success("✅ Estudiante registrado")
    if st.session_state.students:
        st.dataframe(pd.DataFrame(st.session_state.students)[['nombre','id']], use_container_width=True)

elif page == "📝 Limpieza":
    st.subheader("📝 Registro de Limpieza")
    with st.form("form_cleaning"):
        date_input = st.date_input("Fecha:", value=date.today())
        type_cleaning = st.selectbox("Tipo:", ["Aula", "Baños"])
        students_options = [s['nombre'] for s in st.session_state.students]
        selected_students = st.multiselect("Selecciona estudiantes:", students_options)
        submitted = st.form_submit_button("Registrar")
        if submitted:
            if not selected_students:
                st.error("Seleccione al menos un estudiante")
            else:
                record = {
                    'fecha': date_input.strftime('%Y-%m-%d'),
                    'dia_semana': ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][date_input.weekday()],
                    'hora': datetime.now().strftime('%H:%M:%S'),
                    'estudiantes': selected_students,
                    'tipo_limpieza': type_cleaning
                }
                st.session_state.cleaning_history.append(record)
                save_data(st.session_state.cleaning_history, "cleaning_history.json")
                st.success("✅ Registro guardado")
                st.balloons()

elif page == "📊 Historial":
    st.subheader("📊 Historial de Limpieza")
    type_filter = st.selectbox("Tipo:", ["Todos","Aula","Baños"])
    date_range = st.date_input("Rango de fechas:", value=(date.today()-pd.Timedelta(days=7), date.today()))
    
    filtered = st.session_state.cleaning_history
    if type_filter != "Todos":
        filtered = [r for r in filtered if r['tipo_limpieza'] == type_filter]
    filtered = [r for r in filtered if date_range[0] <= datetime.strptime(r['fecha'], '%Y-%m-%d').date() <= date_range[1]]
    
    if filtered:
        df = pd.DataFrame(filtered)
        df['Fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%d/%m/%Y')
        st.dataframe(df[['Fecha','dia_semana','hora','estudiantes','tipo_limpieza']], use_container_width=True)
    else:
        st.info("No hay registros para los filtros seleccionados")

# Footer
st.markdown('<div class="footer">🧹 Sistema de Registro de Limpieza | © 2025 ING. Irvin Adonis Mora Paredes. Todos los derechos reservados.</div>', unsafe_allow_html=True)
