# Pierre the Flutist Robot

En este repositorio se encuentra el codigo necesario para operar el sistema robotico para tocar flauta, Pierre.


Organización del codigo
-----
Los archivos de codigo importantes y su contenido:

| File   |     Content     |
|:--------:|-------------|
| cinematica.py |  clases y funciones para pasar del espacio del robot al de la tarea y viceversa  |
| communication.py | Una clase que se encarga de la mensajería a los distintos dispositivos (usando el protocolo Ethernet IP) de forma centralizada |
| drivers.py | Clases que se encargan con la interacción de los distintos dispositivos: controlador de flujo, sensor de presión, drivers de los motores, driver de los dedos y micrófono |
| GUI.py | Codigo de la ventana principal de la interfaz gráfica |
| manual_move_win.py | Código de la ventana para manejar el robot de forma manual |
| motor_route.py | Código para obtener rutas de 'straight lines' en el espacio de la tarea o de polinamios de tercer orden (al final no se usa) |
| musician.py | Donde se aloja la clase Musician, que funciona como cerebro del robot, coordina las solicitudes del usuario con cada uno de los dispositivos |
| route.py | Código para construir rutas definidas a partir de puntos en cada eje (l, theta, offset, flow y nota) en el tiempo, filtros y vibratos |
| forms/forms.py | Codigo para interpretar la información entregada por el usuario en todos los formularios de la interfaz gráfica |
| lib/ethernet_ip/ethernetip.py | Librería modificada para comunicacion mediante protocolo Ethernet IP. Los cambios estan explicados en el encabezado del archivo |
| plots/plot_window.py | Código de las ventanas que plotean funciones, una que se actualiza en tiempo real (una variable vs la referencia) y otra que no (visualización de la ruta definida y las velocidades en cada eje) |

Cada archivo se encuentra comentado para que sea facil su comprension

Adicionalmente se entregan <a href="https://raw.githack.com/fenahurtado/pierre_flutist/2342e8df5d2afb257ab0c29dc7ef6aa53c4fa293/diagrama.html" target="_blank">diagramas de flujo</a> de todo el codigo para entender mejor su funcionamiento

### PS Move
El programa ocupa el repositorio externo [psmove](https://github.com/thp/psmoveapi).
Este debe ser descargado y se deben hacer los siguientes cambios:
1. Reemplazar el archivo psmoveapi/src/CMakeList.txt por pierre_flutist/src/psmoveapi_mods/CMakeList.txt (o agregar la opcion `option(PSMOVE_BUILD_TRACKER "Enable Tracking" ON)` al CMakeList)
2. Reemplazar el archivo psmoveapi/src/utils/test_tracker.cpp por pierre_flutist/src/psmoveapi_mods/test_tracker.cpp

Luego, se debe compilar el proyecto. Para compilar desde Windows se corre el comando:
`call scripts/visualc/build_msvc.bat 2022 x64` en la *Developer Command Prompt for VS 2022*

Finalmente para correr el script, se corre (dentro de la carpeta del build recien creada) `psmove test-tracker`.