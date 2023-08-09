import streamlit as st
from datetime import datetime
from deta import Deta

# Inicializar Deta
deta = Deta(st.secrets["DETA_KEY"])
tasks_db = deta.Base('tasks_db')
completed_tasks_db = deta.Base('completed_tasks_db')

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
    tasks.sort(key=lambda x: x['due_datetime']) 
    return tasks

def delete_task(task_id):
    tasks_db.delete(task_id)

def update_task(task_id, new_task):
    tasks = get_tasks()
    updated_tasks = []
    for task in tasks:
        if task['task'] == task_id:
            updated_tasks.append({'task': new_task, 'due_datetime': task['due_datetime'].strftime('%Y-%m-%d %H:%M:%S')})
        else:
            updated_tasks.append(task)
    tasks_db.put_many(updated_tasks)

def add_completed_task(task_data):
    task_data['due_datetime'] = task_data['due_datetime'].strftime('%Y-%m-%d %H:%M:%S')
    task_data['completed_datetime'] = task_data['completed_datetime'].strftime('%Y-%m-%d %H:%M:%S')
    completed_tasks_db.put(task_data)
    
def is_task_completed(task_name):
    completed_tasks = completed_tasks_db.fetch().items
    completed_task_names = [task['task'] for task in completed_tasks]
    return task_name in completed_task_names

def main():
    st.title('To-Do List App')

    menu_option = st.sidebar.selectbox('Selecciona una opción', ['Ver tareas pendientes', 'Añadir a la lista', 'Editar la lista', 'Ver historial de tareas completadas'])

    if menu_option == 'Ver tareas pendientes':
        tasks = get_tasks()
        st.header('Tareas Pendientes')
        pending_tasks = [task_data for task_data in tasks if not is_task_completed(task_data['task'])]
        if not pending_tasks:
            st.write('No hay tareas pendientes.')
        else:
            for task_data in pending_tasks:
                st.write(f"**Tarea:** {task_data['task']}")
                st.write(f"**Fecha y Hora:** {task_data['due_datetime']}")
                if st.button(f"completado: {task_data['task']}"):
                    completed_task_data = {
                        'task': task_data['task'],
                        'due_datetime': task_data['due_datetime'],
                        'completed_datetime': datetime.now()
                    }
                    add_completed_task(completed_task_data)
                    delete_task(task_data['task']) 
                    st.success('Tarea marcada como completada.')
                    
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
        tasks = get_tasks()
        st.header('Editar Tarea')
        pending_tasks = [task_data for task_data in tasks if not is_task_completed(task_data['task'])]
        task_names = [task['task'] for task in pending_tasks]
        task_to_edit = st.selectbox('Selecciona la tarea a editar', task_names)
        new_task = st.text_input('Ingresa la nueva tarea')
        
        if st.button('Actualizar tarea'):
            update_task(task_to_edit, new_task)
            st.success('Tarea actualizada con éxito.')

    elif menu_option == 'Ver historial de tareas completadas':
        completed_tasks = completed_tasks_db.fetch().items
        st.header('Historial de Tareas Completadas')
        if not completed_tasks:
            st.write('No hay tareas completadas.')
        else:
            for completed_task in completed_tasks:
                st.write(f"**Tarea:** {completed_task['task']}")
                st.write(f"**Fecha de Completado:** {completed_task['completed_datetime']}")
                st.write('---')


if __name__ == '__main__':
    main()