import streamlit as st
from datetime import datetime
from deta import Deta

# Inicializar Deta
deta = Deta('b0cxuakhz6a_JrrQPS8PTHoC4Fzg6HmnutDzJUFHwdUu')
tasks_db = deta.Base('tasks_db')

def add_task(task, due_datetime):
    task_data = {
        'task': task,
        'due_datetime': due_datetime.strftime('%Y-%m-%d %H:%M:%S')
    }
    tasks_db.put(task_data)

def get_tasks():
    response = tasks_db.fetch()
    tasks = response.items
    for task in tasks:
        task['due_datetime'] = datetime.strptime(task['due_datetime'], '%Y-%m-%d %H:%M:%S')
    return tasks

def update_task(task_id, new_task):
    tasks = get_tasks()
    updated_tasks = []
    for task in tasks:
        if task['task'] == task_id:
            updated_tasks.append({'task': new_task, 'due_datetime': task['due_datetime'].strftime('%Y-%m-%d %H:%M:%S')})
        else:
            updated_tasks.append(task)
    tasks_db.put_many(updated_tasks)

def main():
    st.title('To-Do List App')

    menu_option = st.sidebar.selectbox('Selecciona una opción', ['Ver lista', 'Añadir a la lista', 'Editar la lista'])

    if menu_option == 'Ver lista':
        tasks = get_tasks()
        st.header('Lista de Tareas')
        if not tasks:
            st.write('No hay tareas en la lista.')
        else:
            for task_data in tasks:
                st.write(f"**Tarea:** {task_data['task']}")
                st.write(f"**Fecha y Hora:** {task_data['due_datetime']}")
                st.write('---')

    elif menu_option == 'Añadir a la lista':
        st.header('Añadir Tarea')
        task = st.text_input('Ingresa la tarea')
        due_date = st.date_input('Fecha de vencimiento')
        due_time = st.time_input('Hora de vencimiento')
        due_datetime = datetime.combine(due_date, due_time)
        
        if st.button('Añadir tarea'):
            add_task(task, due_datetime)
            st.success('Tarea añadida con éxito!')

    elif menu_option == 'Editar la lista':
        st.header('Editar Tarea')
        tasks = get_tasks()
        task_names = [task['task'] for task in tasks]
        task_to_edit = st.selectbox('Selecciona la tarea a editar', task_names)
        new_task = st.text_input('Ingresa la nueva tarea')
        
        if st.button('Actualizar tarea'):
            update_task(task_to_edit, new_task)
            st.success('Tarea actualizada con éxito.')

if __name__ == '__main__':
    main()