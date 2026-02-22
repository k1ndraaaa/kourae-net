<<<<<<< HEAD
# kourae
Un pequeño proyecto que estoy haciendo.
=======
# Kourae

Repositorio: https://github.com/loeloevg/kourae.git

Resumen
-------
Kourae es la colección central de microservicios y adaptadores del proyecto. Contiene `microapps/`, `adapters/` y utilidades internas. El directorio `native/` se mantiene fuera del control de versiones público por motivos de seguridad/entorno y aparece en `.gitignore`.

Comunicado de estado
---------------------
Se ha realizado una primera auditoría sobre la lógica interna (contratos y snippets). La documentación está en construcción y el código se alinea a estándares de Python. Se está revisando el rendimiento y la optimización de adaptadores para reducir y economizar consultas.

Importante: en esta etapa no se han considerado aspectos de seguridad web (sesiones, OAuth, HTTP u otras medidas). No se ha hecho auditoría de seguridad para la capa web.