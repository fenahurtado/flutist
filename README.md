# Pierre the Flutist Robot

En este repositorio se encuentra el codigo necesario para operar el sistema robotico para tocar flauta, Pierre.

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
| lib/ethernet_ip/ethernetip.py | Librería modificada para comunicacion mediante protocolo Ethernet IP |
| plots/plot_window.py | Código de las ventanas que plotean funciones, una que se actualiza en tiempo real (una variable vs la referencia) y otra que no (visualización de la ruta definida y las velocidades en cada eje) |