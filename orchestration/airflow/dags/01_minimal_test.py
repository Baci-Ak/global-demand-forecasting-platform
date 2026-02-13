from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

def say_hello():
    print("Hello from PythonOperator in MWAA")
    print("Current date/time:", datetime.now())
    import socket
    print("Hostname:", socket.gethostname())

with DAG(
    dag_id="01_minimal_test",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    t = PythonOperator(
        task_id="python_hello",
        python_callable=say_hello,
    )