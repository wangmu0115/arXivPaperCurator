from airflow import DAG


def hello_world():
    print("Hello from airflow")
    return "success"
