import schedule
import time
from datetime import datetime, timedelta
from twilio.rest import Client
from deta import Deta

# Inicializar Deta
deta = Deta(st.secrets["DETA_KEY"])
tasks_db = deta.Base('tasks_db')

# Configuración de Twilio
account_sid = 'TU_ACCOUNT_SID'
auth_token = 'TU_AUTH_TOKEN'
twilio_phone_number = 'TU_NUMERO_TWILIO'
user_phone_number = 'NUMERO_DESTINO'

def get_pending_tasks_due_today():
    today = datetime.now().date()
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
            message += f"- {task_data['task']}\n"
        
        send_sms(message)

# Programar el envío de mensajes a las 7 AM
schedule.every().day.at("07:00").do(send_daily_task_reminder)

while True:
    schedule.run_pending()
    time.sleep(1)
