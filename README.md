# Kourae-net
---------
Kourae-net es una plantilla de Minio + Postgresql, más una serie de soluciones a partir de esas dos: auth crudo, streaming, anti-payloads, etc. El nombre se lo puse así porque no se me ocurrió otro, lo cambiaré después.

Resumen
---------
Kourae es la colección central de microservicios y adaptadores del proyecto. Contiene `microapps/`, `adapters/` y utilidades internas. El directorio `native/` se mantiene fuera del control de versiones público por motivos de seguridad/entorno y aparece en `.gitignore`.

Comunicado de estado
---------
Se ha realizado una primera auditoría sobre la lógica interna (contratos y snippets). La documentación está en construcción y el código se alinea a estándares de Python. Se está revisando el rendimiento y la optimización de adaptadores para reducir y economizar consultas.

Importante: en esta etapa no se han considerado aspectos de seguridad web (sesiones, OAuth, HTTP u otras medidas). No se ha hecho auditoría de seguridad para la capa web.

Python no será el lenguaje predilecto para el proyecto, sólo es un prototipo.

Comentarios 2026, Febrero 23 para organizarme:
---------
El nombre de "microapps" no expresa nada, es 50% api, 50% infraestructura; ¿qué demonios significa eso? 

Por ejemplo, /adapters sólo concentra servicios third party, habla directamente con las librerías del software externo más la interfaz amigable. Hasta ahí todo genial, se entiende.

Se supone que **kourae-net es una plantilla de Minio + Postgresql, más una serie de soluciones a partir de esas dos: auth crudo, streaming, anti-payloads, etc**. 

Aquí lo dije perfectamente: **más una serie de soluciones**. `/microapps` concentra parte de la infraestructura (creo que son MainClass.py); eso de inmediato hay que cambiarlo a otro path, ¿pero qué nombre le pondré?

Oh, tengo que aclararles algo: No sé para qué chingados sirven los commit, así que uso Initial Commit para el código mismo y uso Update para informes o cambios en README, algo tipo prensa y comunicados.