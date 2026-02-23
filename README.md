# Kourae-net

Kourae-net is a MinIO + PostgreSQL template with some solutions built around those two: native auth, streaming, anti-payload handling, etc. I didn't know what to name it, so yeah, I js put it there (i'ma probably change it later).

About the paths:
---------
`/adapters`: Third Party Services (MinIO, PostgreSQL, Telegram, etc).
`/native`: Helpers and libraries the project needs.
`/microapps`: APIs. It only use the core.

Project status:
---------
An initial audit of the internal logic (contracts and snippets) has been completed. The documentation is still in progress, and the code follows Python standards. It is currently under review for performance improvements and adapter optimization to reduce and simplify queries.

Important: Web security (sessions, OAuth, HTTP protections, etc.) has not been addressed yet. The web layer has not been audited for security.

Python won't be the main language for this project, it's js a prototype lol

Notes 2026, February 23 just for organization (i won't translate this):
---------

El nombre de "microapps" no expresa nada, es 50% api, 50% infraestructura; ¿qué demonios significa eso? 

Por ejemplo, /adapters sólo concentra servicios third party, habla directamente con las librerías del software externo más la interfaz amigable. Hasta ahí todo genial, se entiende.

Se supone que **kourae-net es una plantilla de Minio + Postgresql, más una serie de soluciones a partir de esas dos: auth crudo, streaming, anti-payloads, etc**. 

Aquí lo dije perfectamente: **más una serie de soluciones**. `/microapps` concentra parte de la infraestructura (creo que son MainClass.py); eso de inmediato hay que cambiarlo a otro path, ¿pero qué nombre le pondré?

Oh, a quick reminder: Idfk how to use this commit thing, so i'll use "Initial Commit" for the code updates and "Update" for changes in README, like news or reports.