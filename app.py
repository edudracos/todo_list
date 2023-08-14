import schedule
import time
from datetime import datetime, timedelta
from pytz import timezone
from twilio.rest import Client
import streamlit as st
from deta import Deta

deta = Deta(st.secrets["DETA_KEY"])
tasks_db = deta.Base('tasks_db')
completed_tasks_db = deta.Base('completed_tasks_db')
reminder_config_db = deta.Base('reminder_config_db') 

# Configuración de Twilio
account_sid = st.secrets['ACCOUNT_SID']
auth_token = st.secrets['AUTH_TOKEN']
twilio_phone_number = st.secrets['NUMERO_TWILIO']

time_zone_options = ['America/New_York', 'America/Los_Angeles', 'America/chicago', 'Asia/Tokyo']

if 'time_zone' not in st.session_state:
    st.session_state.time_zone = time_zone_options[0]

if 'reminder_time' not in st.session_state:
    st.session_state.reminder_time = datetime.strptime('07:00', '%H:%M').time()

def get_pending_tasks_due_today():
    today = datetime.now(timezone(st.session_state.time_zone)).date()
    tasks = get_tasks()
    pending_tasks_due_today = [task_data for task_data in tasks if not is_task_completed(task_data['task']) and task_data['due_datetime'].date() == today]
    return pending_tasks_due_today

def send_sms(message):
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=twilio_phone_number,
        to=user_phone_number
    )

def send_daily_task_reminder():
    pending_tasks_due_today = get_pending_tasks_due_today()
    
    if pending_tasks_due_today:
        message = "Tareas pendientes para hoy:\n"
        for task_data in pending_tasks_due_today:
            due_time = task_data['due_datetime'].strftime('%H:%M')
            message += f"- {task_data['task']} (Hora de vencimiento: {due_time})\n"
        
        send_sms(message)
        st.success('Mensaje de recordatorio enviado.')

def add_task(task, due_datetime, description):
    task_data = {
        'task': task,
        'due_datetime': due_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        'description': description
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

def update_task(task_id, new_task, description):
    tasks = get_tasks()
    updated_tasks = []
    for task in tasks:
        if task['task'] == task_id:
            updated_tasks.append({
                'task': new_task,
                'due_datetime': task['due_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                'description': description
            })
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
    st.title('To-Do List & Agenda App')

    menu_option = st.sidebar.selectbox('Selecciona una opción', [
        'Ver tareas pendientes',
        'Añadir a la lista',
        'Editar la lista',
        'Ver historial de tareas completadas'
    ])

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
                if 'description' in task_data:
                    st.write(f"**Descripción:** {task_data['description']}")
                else:
                    st.write("**Descripción:** Sin descripción.")
                if st.button(f"Completado: {task_data['task']}"):
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
        description = st.text_area('Descripción')
        due_date = st.date_input('Fecha de vencimiento')
        due_time = st.time_input('Hora de vencimiento')
        due_datetime = datetime.combine(due_date, due_time)

        if st.button('Añadir tarea'):
            add_task(task, due_datetime, description)
            st.success('Tarea añadida con éxito!')

    elif menu_option == 'Editar la lista':
        tasks = get_tasks()
        st.header('Editar Tarea')
        pending_tasks = [task_data for task_data in tasks if not is_task_completed(task_data['task'])]
        task_names = [task['task'] for task in pending_tasks]
        task_to_edit = st.selectbox('Selecciona la tarea a editar', task_names)
        new_task = st.text_input('Ingresa la nueva tarea')
        new_description = st.text_area('Nueva descripción')

        if st.button('Actualizar tarea'):
            update_task(task_to_edit, new_task, new_description)
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

    if st.sidebar.checkbox('Configuración de Recordatorios'):
        st.header('Configuración de Recordatorios')
        time_zone = st.selectbox('Selecciona tu zona horaria', time_zone_options, index=time_zone_options.index(st.session_state.time_zone))

        # Obtener la configuración actual de recordatorios del usuario
        user_config = reminder_config_db.get('user_config')
        if user_config is None:
            user_config = {'phone_number': '', 'reminder_time': datetime.strptime('07:00', '%H:%M').time()}
        else:
            user_config['reminder_time'] = datetime.strptime(user_config['reminder_time'], '%H:%M').time()

        # Mostrar los campos para la configuración
        phone_number = st.text_input('Número de teléfono para recibir mensajes', value=user_config['phone_number'])
        reminder_time = st.time_input('Hora de recordatorio diario', value=user_config['reminder_time'])

        if st.button('Guardar configuración'):
            # Guardar la configuración en la base de datos
            user_config['phone_number'] = phone_number
            user_config['reminder_time'] = reminder_time.strftime('%H:%M')
            reminder_config_db.put(user_config, 'user_config')
            st.session_state.time_zone = time_zone
            st.success('Configuración guardada.')

    if st.sidebar.checkbox('Control de Recordatorio'):
        st.header('Control de Recordatorio')
        reminder_status = st.session_state.get('reminder_status', False)

        if reminder_status:
            st.write('El recordatorio diario está activado.')
            if st.button('Cancelar Recordatorio'):
                st.session_state.reminder_status = False
                st.success('Recordatorio cancelado.')
        else:
            st.warning('El recordatorio diario está desactivado.')
            if st.button('Iniciar Recordatorio'):
                st.session_state.reminder_status = True
                st.success('Recordatorio iniciado. Revise su teléfono para recibir mensajes de recordatorio.')


if __name__ == '__main__':
    main()

# Programar el envío de mensajes según la hora configurada
def schedule_daily_task_reminder():
    reminder_status = st.secrets.get('REMINDER_STATUS', False)
    if reminder_status:
        reminder_time = datetime.strptime(st.secrets['REMINDER_TIME'], '%H:%M').time()
        schedule.every().day.at(reminder_time.strftime('%H:%M')).do(send_daily_task_reminder)

    while True:
        schedule.run_pending()
        time.sleep(1)