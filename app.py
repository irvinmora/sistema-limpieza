import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import os

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Registro de Limpieza",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    except Exception as e:
        st.error(f"Error al guardar: {e}")
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

def update_cleaning_records_after_deletion(student_name):
    """Elimina al estudiante de todos los registros de limpieza donde aparece"""
    updated_records = []
    for record in st.session_state.cleaning_history:
        updated_students = [s for s in record['estudiantes'] if s != student_name]
        if updated_students:  # Solo mantener registros que aún tengan estudiantes
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
st.markdown('<h1 style="text-align: center; color: red; font-size: 3rem;">🧹 Sistema de Registro de Limpieza</h1>', unsafe_allow_html=True)

# Navegación basada en estado de sesión
page = st.session_state.page

# Página de Registro de Estudiantes - ELIMINACIÓN COMPLETAMENTE CORREGIDA
if page == "👥 Registro de Estudiantes":
    st.markdown('<h2 style="color: blue; border-bottom: 2px solid blue;">👥 Gestión de Estudiantes</h2>', unsafe_allow_html=True)
    
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
    st.markdown('<h2 style="color: blue; border-bottom: 2px solid blue;">📋 Lista de Estudiantes</h2>', unsafe_allow_html=True)
    
    if st.session_state.students:
        students_df = pd.DataFrame(st.session_state.students)
        display_df = students_df[['nombre', 'id']].copy()
        st.dataframe(display_df, use_container_width=True)
        
        # Gestión de estudiantes (Editar/Eliminar) - ELIMINACIÓN COMPLETAMENTE NUEVA
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
                    st.warning(f"⚠️ Este estudiante aparece en {cleaning_count} registros de limpieza.")
                    st.info("El estudiante será eliminado de todos los registros de limpieza donde aparece.")
            
            # ELIMINACIÓN DIRECTA Y FUNCIONAL
            if student_to_delete:
                st.error("🚨 **ADVERTENCIA:** Esta acción no se puede deshacer.")
                
                # Usar un form para la eliminación para evitar problemas de estado
                with st.form(f"delete_form_{student_to_delete}"):
                    confirm = st.checkbox("✅ Confirmo que quiero eliminar este estudiante", 
                                        key=f"confirm_{student_to_delete}")
                    
                    if st.form_submit_button("🔥 ELIMINAR ESTUDIANTE", type="primary"):
                        if confirm:
                            try:
                                # 1. Guardar el nombre del estudiante a eliminar
                                student_name_to_delete = student_to_delete
                                
                                # 2. Eliminar estudiante de la lista principal
                                nuevos_estudiantes = [s for s in st.session_state.students 
                                                    if s['nombre'] != student_name_to_delete]
                                
                                # 3. Actualizar registros de limpieza
                                nuevos_registros = update_cleaning_records_after_deletion(student_name_to_delete)
                                
                                # 4. Actualizar el estado de la sesión
                                st.session_state.students = nuevos_estudiantes
                                st.session_state.cleaning_history = nuevos_registros
                                
                                # 5. Guardar en archivos
                                success1 = save_data(nuevos_estudiantes, "students.json")
                                success2 = save_data(nuevos_registros, "cleaning_history.json")
                                
                                if success1 and success2:
                                    st.success(f"✅ Estudiante '{student_name_to_delete}' eliminado exitosamente!")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al guardar los cambios en los archivos.")
                                    
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {str(e)}")
                        else:
                            st.warning("❌ Debes confirmar la eliminación marcando la casilla.")
    
    else:
        st.info("📝 No hay estudiantes registrados aún.")

# Otras páginas (simplificadas para el ejemplo)
elif page == "🏠 Inicio":
    st.markdown('<h2 style="color: blue;">Bienvenido al Sistema de Registro de Limpieza</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Estudiantes", len(st.session_state.students))
    col2.metric("Registros de Limpieza", len(st.session_state.cleaning_history))
    
    # Mostrar archivos guardados
    st.info("📁 Archivos guardados:")
    if os.path.exists("data/students.json"):
        st.write("✅ students.json - Guardado correctamente")
    else:
        st.write("❌ students.json - No existe")
    
    if os.path.exists("data/cleaning_history.json"):
        st.write("✅ cleaning_history.json - Guardado correctamente")
    else:
        st.write("❌ cleaning_history.json - No existe")

elif page == "📝 Registro de Limpieza":
    st.markdown('<h2 style="color: blue;">📝 Registro de Limpieza Diaria</h2>', unsafe_allow_html=True)
    
    with st.form("cleaning_form"):
        col1, col2 = st.columns(2)
        with col1:
            cleaning_date = st.date_input("Fecha de limpieza:", value=date.today())
            cleaning_type = st.selectbox("Tipo de limpieza:", ["Aula", "Baños"])
        with col2:
            available_students = [s['nombre'] for s in st.session_state.students]
            if available_students:
                st.write("Selecciona estudiantes:")
                student1 = st.selectbox("Estudiante 1:", [""] + available_students)
                student2 = st.selectbox("Estudiante 2:", [""] + available_students)
            else:
                st.error("No hay estudiantes registrados")
        
        if st.form_submit_button("Registrar Limpieza"):
            students_selected = [s for s in [student1, student2] if s]
            if students_selected:
                new_record = {
                    'fecha': cleaning_date.strftime('%Y-%m-%d'),
                    'estudiantes': students_selected,
                    'tipo_limpieza': cleaning_type,
                    'hora': datetime.now().strftime('%H:%M:%S')
                }
                st.session_state.cleaning_history.append(new_record)
                if save_data(st.session_state.cleaning_history, "cleaning_history.json"):
                    st.success("✅ Limpieza registrada!")
                    st.rerun()

elif page == "📊 Historial de Limpieza":
    st.markdown('<h2 style="color: blue;">📊 Historial de Limpieza</h2>', unsafe_allow_html=True)
    
    if st.session_state.cleaning_history:
        history_df = pd.DataFrame(st.session_state.cleaning_history)
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No hay registros de limpieza")

# Footer
st.markdown("---")
st.markdown("**Sistema de Registro de Limpieza** 🧹")