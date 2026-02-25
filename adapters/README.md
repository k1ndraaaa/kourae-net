# Adapters

Hablemos de los adapters. A diferencia de un bundle como XAMPP, Todo se trabaja dentro del lenguaje a usar, como si fuese un framework. Los adaptadores viven sí o sí de la librería más estandarizada, imparcial o "de bajo nivel" de un entorno. Estos adaptadores son clases con métodos básicos (no ejecutan lógica de aplicación) que puentean con el software externo relacionado. He aquí de mostrar algunos adaptadores en Python con sus respectivas librerías:

`/Postgresql` -> psycopg2, psycopg2-binary

`/Redis` -> redis

`/Minio` -> minio

`/Telegram` -> telethon

En resumidas cuentas, se hace una interfaz preparada dentro del lenguaje con la configuración inicial que la librería solicita.

Para usar una clase, revise el contrato de la clase a usar.