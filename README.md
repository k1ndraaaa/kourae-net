# Kourae-net

Kourae-net es una plantilla de Minio + Postgresql + Redis, más una serie de soluciones a partir de esas dos: auth crudo, streaming, anti-payloads, cacheo, economización de consultas, etc. El nombre se lo puse así porque no se me ocurrió otro, lo cambiaré después.

Sobre los paths:
---------
`/adapters`: Servicios de terceros (MinIO, PostgreSQL, Redis, Telegram, etc).
`/native`: Helpers y bibliotecas de apoyo que sí o sí usa todo el proyecto.

Comunicado de estado:
---------
Se ha realizado una primera auditoría sobre la lógica interna (contratos y snippets). La documentación está en construcción y el código se alinea a estándares de Python. Se está revisando el rendimiento y la optimización de adaptadores para reducir y economizar consultas.

Importante: en esta etapa no se han considerado aspectos de seguridad web (sesiones, OAuth, HTTP u otras medidas). No se ha hecho auditoría de seguridad para la capa web.

Python no será el lenguaje predilecto para el proyecto, sólo es un prototipo.