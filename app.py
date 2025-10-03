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
    PDF_AVAILABLE = False

# Estilos CSS personalizados
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# FUNCIONES MEJORADAS PARA MANEJO DE DATOS
def load_data(filename):
    try:
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{filename}"
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
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
    if 'editing_student' not in st.session_state:
        st.session_state.editing_student = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Inicio"
    # Estado para eliminación
    if 'delete_confirmed' not in st.session_state:
        st.session_state.delete_confirmed = False
    if 'student_to_delete' not in st.session_state:
        st.session_state.student_to_delete = None

def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece"""
    updated_records = []
    for record in st.session_state.cleaning_history:
        updated_students = [s for s in record['estudiantes'] if s != student_name]
        if updated_students:
            record['estudiantes'] = updated_students
            updated_records.append(record)
    return updated_records

# Inicializar estado de la sesión
initialize_session_state()

# MENÚ DE NAVEGACIÓN
with st.sidebar:
    st.markdown("## 🧭 Menú de Navegación")
    st.markdown("---")
    
    if st.button("🏠 **INICIO**", use_container_width=True):
        st.session_state.page = "🏠 Inicio"
        st.rerun()
        
    if st.button("👥 **REGISTRO DE ESTUDIANTES**", use_container_width=True):
        st.session_state.page = "👥 Registro de Estudiantes"
        st.rerun()
        
    if st.button("📝 **REGISTRO DE LIMPIEZA**", use_container_width=True):
        st.session_state.page = "📝 Registro de Limpieza"
        st.rerun()
        
    if st.button("📊 **HISTORIAL DE LIMPIEZA**", use_container_width=True):
        st.session_state.page = "📊 Historial de Limpieza"
        st.rerun()

# Encabezado principal
st.markdown('<h1 class="main-header">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Navegación basada en estado de sesión
page = st.session_state.page

# Página de Registro de Estudiantes - CÓDIGO CORREGIDO
if page == "👥 Registro de Estudiantes":
    st.markdown('<h2 class="section-header">👥 Gestión de Estudiantes</h2>', unsafe_allow_html=True)
    
    # Formulario para agregar/editar estudiantes
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
                    
                    existing_names = [s['nombre'].upper() for s in st.session_state.students if s['nombre'] != old_name]
                    if student_name.upper() in existing_names:
                        st.error("❌ Ya existe otro estudiante con ese nombre.")
                    else:
                        for student in st.session_state.students:
                            if student['nombre'] == old_name:
                                student['nombre'] = student_name
                                student['id'] = student_id.strip() if student_id else old_id
                                break
                        
                        if save_data(st.session_state.students, "students.json"):
                            st.success("✅ Estudiante actualizado exitosamente!")
                            st.session_state.edit_mode = False
                            st.session_state.editing_student = None
                            st.rerun()
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
                            st.rerun()
            else:
                st.error("❌ Por favor ingresa un nombre válido.")
    
    # Lista de estudiantes registrados
    st.markdown('<h2 class="section-header">📋 Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        display_df = students_df[['nombre', 'id']].copy()
        st.dataframe(display_df, use_container_width=True)
        
        # Gestión de estudiantes (Editar/Eliminar) - CÓDIGO CORREGIDO
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
                cleaning_count = sum(1 for record in st.session_state.cleaning_history 
                                   if student_to_delete in record['estudiantes'])
                
                if cleaning_count > 0:
                    st.warning(f"⚠️ **Advertencia:** Este estudiante aparece en **{cleaning_count}** registros de limpieza.")
                    st.info("💡 **Nota:** El estudiante será eliminado de todos los registros de limpieza donde aparece.")
            
            # BOTÓN DE ELIMINACIÓN SIMPLIFICADO - CORREGIDO
            if st.button("❌ Eliminar Estudiante", type="secondary", key="delete_button"):
                st.session_state.student_to_delete = student_to_delete
                st.session_state.delete_confirmed = False
                st.rerun()
            
            # CONFIRMACIÓN DE ELIMINACIÓN - CORREGIDO
            if st.session_state.student_to_delete == student_to_delete:
                st.error("🚨 **¡ADVERTENCIA!** Esta acción eliminará al estudiante de todos los registros de limpieza.")
                
                # Checkbox de confirmación
                confirm = st.checkbox("✅ Confirmo que quiero eliminar este estudiante y quitarlo de todos los registros de limpieza", 
                                    key="confirm_delete")
                
                # Botón de confirmación final
                if confirm:
                    if st.button("🔥 CONFIRMAR ELIMINACIÓN DEFINITIVA", type="primary", key="final_delete"):
                        # Guardar el nombre antes de eliminar
                        student_name_to_delete = st.session_state.student_to_delete
                        
                        # Eliminar estudiante de la lista
                        st.session_state.students = [s for s in st.session_state.students 
                                                   if s['nombre'] != student_name_to_delete]
                        
                        # Actualizar registros de limpieza
                        st.session_state.cleaning_history = update_cleaning_records_after_deletion(student_name_to_delete)
                        
                        # Guardar cambios en ambos archivos
                        success1 = save_data(st.session_state.students, "students.json")
                        success2 = save_data(st.session_state.cleaning_history, "cleaning_history.json")
                        
                        if success1 and success2:
                            st.success("✅ Estudiante eliminado exitosamente!")
                            # Limpiar estado de eliminación
                            st.session_state.student_to_delete = None
                            st.session_state.delete_confirmed = False
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar el estudiante.")
    
    else:
        st.info("📝 No hay estudiantes registrados aún.")

# Otras páginas (Inicio, Registro de Limpieza, Historial) permanecen igual...
elif page == "🏠 Inicio":
    st.markdown('<h2 class="section-header">Bienvenido al Sistema de Registro de Limpieza</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Estudiantes", len(st.session_state.students))
    col2.metric("Registros de Limpieza", len(st.session_state.cleaning_history))
    col3.metric("Limpiezas Esta Semana", len([r for r in st.session_state.cleaning_history]))

elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 class="section-header">📝 Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    
    with st.form("cleaning_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today())
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"])
        with col2:
            available_students = [s['nombre'] for s in st.session_state.students]
            if available_students:
                st.write("Selecciona los estudiantes (1-3):")
                student1 = st.selectbox("Estudiante 1:", [""] + available_students)
                student2 = st.selectbox("Estudiante 2 (opcional):", [""] + available_students)
                student3 = st.selectbox("Estudiante 3 (opcional):", [""] + available_students)
            else:
                st.error("❌ No hay estudiantes registrados. Primero registra estudiantes.")
        
        submitted = st.form_submit_button("Registrar Limpieza")
        
        if submitted and available_students:
            students_selected = [s for s in [student1, student2, student3] if s]
            if students_selected:
                new_record = {
                    'fecha': cleaning_date.strftime('%Y-%m-%d'),
                    'dia_semana': ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][cleaning_date.weekday()],
                    'hora': datetime.now().strftime('%H:%M:%S'),
                    'estudiantes': students_selected,
                    'tipo_limpieza': cleaning_type
                }
                st.session_state.cleaning_history.append(new_record)
                if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                    st.success("✅ Limpieza registrada exitosamente!")
                    st.rerun()

elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 class="section-header">📊 Historial de Limpieza</h2>', unsafe_allow_html=True)
    
    if st.session_state.cleaning_history:
        history_df = pd.DataFrame(st.session_state.cleaning_history)
        history_df['Fecha'] = pd.to_datetime(history_df['fecha']).dt.strftime('%d/%m/%Y')
        display_df = history_df[['Fecha', 'dia_semana', 'hora', 'estudiantes', 'tipo_limpieza']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No hay registros de limpieza.")

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