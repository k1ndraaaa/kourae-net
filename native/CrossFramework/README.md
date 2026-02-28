La intención de este CrossFramework es bajar la exclusividad y contexto independiente de cada framework (en este caso Flask, Django, etc) a algo más estandar o Kouraeizado.

El objeto Request de Kourae me puede ayudar demasiado para crear un futuro ExpectedDataForm o otras chingaderas que se me ocurran y me faciliten el desarrollo de mis servicios.

Como podrán ver, hice una interfaz para traducir el Request de Flask. Planeo hacer un sistema de bloques para que puedan traducir otros objetos rápido. No sé cómo decirlo.

Ahorita hice 3 traductores: django, flask, fastapi porque es lo más usado. Lo siguiente a hacer es una plantilla Traductor que respete el mismo contrato de las 3, así será más escalable construir un traductor.