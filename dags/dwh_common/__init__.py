"""
Código compartido por los DAGs del DWH.

Este paquete NO importa Airflow: contiene la configuración de los DAGs
y las funciones (callables) que ejecuta cada PythonOperator. Así se
puede testear en el CI sin instalar Airflow.
"""
