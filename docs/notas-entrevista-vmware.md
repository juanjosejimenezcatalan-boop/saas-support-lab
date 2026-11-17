# Notas de entrevista · Ampliación VMware

## Qué aporta esta práctica

La API y PostgreSQL se ejecutan dentro de Ubuntu en VMware Fusion. El Mac realiza
las peticiones por la red privada. Esto amplía las comprobaciones anteriores,
que se hacían dentro del mismo sistema operativo.

## Decisiones y razonamiento

- **ARM64** corresponde a la arquitectura del Mac Apple Silicon. Una imagen
  x86 no es intercambiable con esta imagen.
- **Dos CPU y 4 GiB de RAM** bastan para este caso pequeño y dejan recursos al Mac.
- **Disco virtual de 24 GiB con asignación dinámica** da espacio al sistema sin
  reservar toda esa capacidad física desde el principio.
- **NAT** permite al invitado descargar paquetes y al Mac consultar la IP privada.
  El laboratorio no configura reenvío de puertos del router ni modo puente.
- **Cloud-init** describe el arranque inicial y hace visible cómo se prepara el
  usuario, los paquetes y la aplicación. Hay que esperar su finalización antes
  de reiniciar.
- **SSH con clave** permite administrar Linux y revisar sus registros desde el Mac.
  La clave privada y los discos se conservan fuera del repositorio.
- **systemd** mantiene una definición del servicio, permite pararlo y arrancarlo,
  y centraliza sus registros en el journal.
- **Flask en 0.0.0.0 dentro de la VM** permite recibir peticiones por su adaptador.
  El 127.0.0.1 del Mac y el de Ubuntu pertenecen a sistemas distintos.
- **PostgreSQL por socket local** evita necesitar un puerto de base de datos
  accesible desde el Mac. Solo la API consulta la base dentro del invitado.

Ubuntu instala PostgreSQL 16 desde sus repositorios. El laboratorio original del
Mac usa 17. El esquema y las consultas de este ejercicio son compatibles con
ambos. Debo indicar la versión realmente utilizada cuando explique la práctica.

## Cómo explicar un fallo

Primero compruebo que la VM está encendida. Después reviso su dirección y ruta,
la conexión TCP, la respuesta HTTP y el registro de la aplicación. Que SSH
funcione mientras el puerto 8000 rechaza conexiones orienta la investigación
hacia el servicio, su puerto o su dirección de escucha.

Una respuesta 404 para LAB-999 es el comportamiento esperado. Para LAB-001,
compruebo tanto el 200 como el identificador y el estado devueltos. La nueva
base empieza en received, independientemente del published del ejercicio
resuelto en el Mac.

## Snapshots

Un snapshot conserva un punto de recuperación de esta VM. Revertirlo también
revierte los cambios de la base de datos posteriores. Por eso la prueba utiliza
un archivo de marcador desechable y una VM dedicada al laboratorio.

La validación debe demostrar tres cosas: el marcador existe después del snapshot,
ha desaparecido al restaurarlo y la API vuelve a responder correctamente. Un
snapshot depende de sus discos base y no sustituye a una copia independiente.

## Respuesta breve para una entrevista

«Amplié el laboratorio a Ubuntu ARM64 en VMware Fusion. Separé el cliente en el
Mac de la aplicación y la base en el invitado. Configuré red NAT, administración
por SSH y un servicio systemd. Comprobé las respuestas desde el Mac y documenté
cómo distinguir un servicio detenido de un fallo de conexión a PostgreSQL.
El registro de validación indica qué pruebas de recuperación se completaron».

Esta ampliación fue implementada con ayuda de un asistente. Para defenderla en
una entrevista debo poder reproducir los comandos, interpretar sus resultados
y explicar el alcance de cada comprobación. La práctica utiliza Fusion local;
la administración de ESXi y vCenter requiere ejercicios específicos adicionales.

## Evidencia

Consultar [el registro de validación](../vmware/validation.md) para los resultados
observados. La guía de reproducción está en [VMware](../vmware/README.md).
