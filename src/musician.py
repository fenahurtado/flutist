from multiprocessing import Process, Event, Value, Pipe
import time
import pandas as pd
from src.drivers import DATA, AMCIDriver, INPUT_FUNCTION_BITS, FlowControllerDriver, FingersDriver, PressureSensor, Microphone
from src.communication import CommunicationCenter
from src.motor_route import *
from src.route import *
from src.cinematica import *

class Musician(Process):
    def __init__(self, host, connections, running, end_pipe, data, interval=0.01, home=True, x_connect=True, z_connect=True, alpha_connect=True, flow_connect=True, fingers_connect=True, pressure_sensor_connect=True, mic_connect=True):
        Process.__init__(self) # Initialize the threading superclass
        global DATA
        self.t0 = time.time()
        self.host = host
        self.running = running
        self.end_pipe = end_pipe
        self.interval = interval
        self.x_connect = x_connect
        self.z_connect = z_connect
        self.alpha_connect = alpha_connect
        self.flow_connect = flow_connect
        self.fingers_connect = fingers_connect
        self.pressure_sensor_connect = pressure_sensor_connect
        self.mic_connect = mic_connect
        self.connections = connections
        self.home = home
        self.instrument = 'flute'
        self.data = data
        
        self.loaded_route_x = []
        self.loaded_route_z = []
        self.loaded_route_alpha = []
        self.loaded_route_flow = []
        self.loaded_route_notes = []
    
    def run(self):
        global DATA
        print("Running musician...")

        if self.x_connect or self.z_connect or self.alpha_connect or self.flow_connect or self.pressure_sensor_connect:
            communication_connect = True
        else:
            communication_connect = False

        print("Connecting communications...")
        self.comm_event = Event()
        self.comm_event.set()
        self.comm_pipe, comm_pipe2 = Pipe()
        self.communications = CommunicationCenter(self.host, self.comm_event, comm_pipe2, self.data, connect=communication_connect, verbose=False)
        self.communications.start()
        print("Communication started...\nConnecting Drivers...")
        print(DATA)

        self.x_driver_conn, x_driver_end_conn = Pipe()
        self.x_virtual_axis_conn, x_virtual_axis_end_conn = Pipe()

        self.x_driver = AMCIDriver(self.connections[0], self.running, x_driver_end_conn, self.comm_pipe, self.data, x_virtual_axis_end_conn, self.t0, connected=self.x_connect, starting_speed=1, verbose=False, input_2_function_bits=INPUT_FUNCTION_BITS['CW Limit'], virtual_axis_follow_acceleration=DATA['x_control']['acceleration'], virtual_axis_follow_deceleration=DATA['x_control']['deceleration'], home=self.home, use_encoder_bit=1, motor_current=30, virtual_axis_proportional_coef=DATA['x_control']['proportional_coef'], encoder_pulses_turn=4000, motors_step_turn=4000, hybrid_control_gain=0, enable_stall_detection_bit=0, current_loop_gain=1, Kp=DATA['x_control']['kp'], Ki=DATA['x_control']['ki'], Kd=DATA['x_control']['kd'], Kp_vel=DATA['x_control']['kp_vel'], Ki_vel=DATA['x_control']['ki_vel'], Kd_vel=DATA['x_control']['kd_vel'])
        
        self.z_driver_conn, z_driver_end_conn = Pipe()
        self.z_virtual_axis_conn, z_virtual_axis_end_conn = Pipe()

        self.z_driver = AMCIDriver(self.connections[1], self.running, z_driver_end_conn, self.comm_pipe, self.data, z_virtual_axis_end_conn, self.t0, connected=self.z_connect, starting_speed=1, verbose=False, input_2_function_bits=INPUT_FUNCTION_BITS['CW Limit'], virtual_axis_follow_acceleration=DATA['z_control']['acceleration'], virtual_axis_follow_deceleration=DATA['z_control']['deceleration'], home=self.home, use_encoder_bit=1, motor_current=30, virtual_axis_proportional_coef=DATA['z_control']['proportional_coef'], encoder_pulses_turn=4000, motors_step_turn=4000, hybrid_control_gain=0, enable_stall_detection_bit=0, current_loop_gain=1, Kp=DATA['z_control']['kp'], Ki=DATA['z_control']['ki'], Kd=DATA['z_control']['kd'], Kp_vel=DATA['z_control']['kp_vel'], Ki_vel=DATA['z_control']['ki_vel'], Kd_vel=DATA['z_control']['kd_vel'])
        
        self.alpha_driver_conn, alpha_driver_end_conn = Pipe()
        self.alpha_virtual_axis_conn, alpha_virtual_axis_end_conn = Pipe()
        
        self.alpha_driver = AMCIDriver(self.connections[2], self.running, alpha_driver_end_conn, self.comm_pipe, self.data, alpha_virtual_axis_end_conn, self.t0, connected=self.alpha_connect, starting_speed=1, verbose=False, input_2_function_bits=INPUT_FUNCTION_BITS['CCW Limit'], virtual_axis_follow_acceleration=DATA['alpha_control']['acceleration'], virtual_axis_follow_deceleration=DATA['alpha_control']['deceleration'], home=self.home, use_encoder_bit=1, motor_current=30, virtual_axis_proportional_coef=DATA['alpha_control']['proportional_coef'], encoder_pulses_turn=4000, motors_step_turn=4000, hybrid_control_gain=0, enable_stall_detection_bit=0, current_loop_gain=1, Kp=DATA['alpha_control']['kp'], Ki=DATA['alpha_control']['ki'], Kd=DATA['alpha_control']['kd'], Kp_vel=DATA['alpha_control']['kp_vel'], Ki_vel=DATA['alpha_control']['ki_vel'], Kd_vel=DATA['alpha_control']['kd_vel'])

        self.flow_driver_conn, flow_driver_end_conn = Pipe()
        self.virtual_flow_conn, virtual_flow_end_conn = Pipe()
        self.flow_driver = FlowControllerDriver(self.connections[3], self.running, self.t0, flow_driver_end_conn, self.comm_pipe, self.data, virtual_flow_end_conn, connected=self.flow_connect, verbose=False)

        self.fingers_driver_conn, fingers_driver_end_conn = Pipe()
        self.virtual_fingers_conn, virtual_fingers_end_conn = Pipe()
        
        self.fingers_driver = FingersDriver(self.connections[5], self.running, fingers_driver_end_conn, virtual_fingers_end_conn, self.t0, connected=self.fingers_connect, verbose=False)
        # self.virtual_fingers_driver_conn, virtual_fingers_driver_end_conn = Pipe()
        # self.virtual_fingers = VirtualFingers(self.running, 0.05, self.t0, self.fingers_driver, virtual_fingers_driver_end_conn, verbose=True)

        self.preasure_sensor_conn, preasure_sensor_end_conn = Pipe()
        self.preasure_sensor = PressureSensor(self.connections[4], self.running, preasure_sensor_end_conn, self.comm_pipe, self.data, connected=self.pressure_sensor_connect, verbose=True)
        
        self.mic_conn, mic_end_conn = Pipe()
        self.mic_running = Event()
        self.microphone = Microphone(self.running, mic_end_conn, DATA['frequency_detection']['device'], DATA['frequency_detection']['method'], DATA['frequency_detection']['YIN'], DATA['frequency_detection']['pYIN'], self.mic_running, connected=self.mic_connect, verbose=False)

        print("Drivers created...\nCreating memory...")

        self.memory_conn, memory_end_conn = Pipe()
        self.memory = Memory(self.running, self.x_driver, self.z_driver, self.alpha_driver, self.flow_driver, self.preasure_sensor, self.microphone, memory_end_conn, self.data, windowWidth=200, interval=0.01)

        print("Memory created...\nStarting...")

        self.memory.start()

        # self.fingers_driver.start()
        # self.virtual_fingers.start()
        
        self.x_driver.start()
        self.z_driver.start()
        self.alpha_driver.start()
        self.flow_driver.start()
        self.fingers_driver.start()
        self.preasure_sensor.start()

        self.microphone.start()

        self.special_command_clicked = False

        self.end_pipe.send(['instances created'])
        print("Pierre started listening...")

        devices_connected = 0
        while True:
            if devices_connected == 8:
                break
            elif self.x_driver_conn.poll():
                message = self.x_driver_conn.recv()
                if message[0] == "driver_started":
                    devices_connected += 1
                    self.end_pipe.send(["x_driver_started"])
            elif self.z_driver_conn.poll():
                message = self.z_driver_conn.recv()
                if message[0] == "driver_started":
                    devices_connected += 1
                    self.end_pipe.send(["z_driver_started"])
            elif self.alpha_driver_conn.poll():
                message = self.alpha_driver_conn.recv()
                if message[0] == "driver_started":
                    devices_connected += 1
                    self.end_pipe.send(["alpha_driver_started"])
            elif self.memory_conn.poll():
                message = self.memory_conn.recv()
                if message[0] == "memory_started":
                    devices_connected += 1
                    self.end_pipe.send(["memory_started"])
            elif self.mic_conn.poll():
                message = self.mic_conn.recv()
                if message[0] == "microphone_started":
                    devices_connected += 1
                    self.end_pipe.send(["microphone_started"])
            elif self.flow_driver_conn.poll():
                message = self.flow_driver_conn.recv()
                if message[0] == "flow_driver_started":
                    devices_connected += 1
                    self.end_pipe.send(["flow_driver_started"])
            elif self.preasure_sensor_conn.poll():
                message = self.preasure_sensor_conn.recv()
                if message[0] == "pressure_sensor_started":
                    devices_connected += 1
                    self.end_pipe.send(["pressure_sensor_started"])
            elif self.fingers_driver_conn.poll():
                message = self.fingers_driver_conn.recv()
                if message[0] == "finger_driver_started":
                    devices_connected += 1
                    self.end_pipe.send(["finger_driver_started"])

        while self.running.is_set():
            if self.end_pipe.poll():
                message = self.end_pipe.recv()
                if message[0] == "get_memory_data":
                    self.memory_conn.send(["get_data"])
                    data = self.memory_conn.recv()[0]
                    print(data)
                    self.end_pipe.send([data])
                elif message[0] == "get_ref_state":
                    s = self.get_ref_state()
                    print(s)
                    self.end_pipe.send([s])
                elif message[0] == "execute_fingers_action":
                    self.virtual_fingers_conn.send(["merge_ref", [(0, message[1])]])
                elif message[0] == "move_to":
                    self.move_to(message[1], T=message[2], only_x=message[3], only_z=message[4], only_alpha=message[5], only_flow=message[6], speed=message[7])
                elif message[0] == "move_to_final":
                    desired = message[1]
                    self.x_virtual_axis_conn.send(["merge_ref", [(0, mm2units(desired.x), 0)]])
                    self.z_virtual_axis_conn.send(["merge_ref", [(0, mm2units(desired.z), 0)]])
                    self.alpha_virtual_axis_conn.send(["merge_ref", [(0, angle2units(desired.alpha), 0)]])
                    self.virtual_flow_conn.send(["merge_ref", [(0, desired.flow)], 0, 0])
                elif message[0] == "reset_x_controller":
                    pass #self.reset_x_controller()
                elif message[0] == "reset_z_controller":
                    pass #self.reset_z_controller()
                elif message[0] == "reset_alpha_controller":
                    pass #self.reset_alpha_controller()
                elif message[0] == "load_routes":
                    self.loaded_route_x = message[1]
                    self.loaded_route_z = message[2]
                    self.loaded_route_alpha = message[3]
                    self.loaded_route_flow = message[4]
                    self.loaded_route_notes = message[5]
                elif  message[0] == "start_loaded_script":
                    if message[1]:
                        self.memory_conn.send(["start_saving"])
                        self.mic_conn.send(["start_saving"])
                    self.start_loaded_script()
                elif message[0] == "stop_playing":
                    self.stop()
                    if message[1]:
                        self.memory_conn.send(["stop_recording"])
                        self.mic_conn.send(["stop_recording"])
                elif  message[0] == "execute_score":
                    self.execute_score(message[1])
                    print("executed")
                elif message[0] == "stop":
                    self.stop()
                    self.memory_conn.send(["stop_recording"])
                    self.mic_conn.send(["stop_recording"])
                elif message[0] == "memory.save_recorded_data":
                    self.memory_conn.send(["save_recorded_data", message[1]])
                    self.mic_conn.send(["save_recorded_data", message[2]])
                elif message[0] == "flow_driver.change_controlled_var":
                    self.flow_driver_conn.send(["change_controlled_var", message[1]])
                elif message[0] == "flow_driver.change_control_loop":
                    self.flow_driver_conn.send(["change_control_loop", message[1]])
                elif message[0] == "flow_driver.change_kp":
                    self.flow_driver_conn.send(["change_kp", message[1]])
                elif message[0] == "flow_driver.change_ki":
                    self.flow_driver_conn.send(["change_ki", message[1]])
                elif message[0] == "flow_driver.change_kd":
                    self.flow_driver_conn.send(["change_kd", message[1]])
                elif message[0] == "set_instrument":
                    self.set_instrument(message[1])
                elif message[0] == "x_driver.ask_control":
                    self.x_driver_conn.send(["ask_control"])
                    data = self.x_driver_conn.recv()[0]
                    self.end_pipe.send([data])
                elif message[0] == "x_driver.change_control":
                    self.x_driver_conn.send(["change_control", message[1]])
                elif message[0] == "z_driver.ask_control":
                    self.z_driver_conn.send(["ask_control"])
                    data = self.z_driver_conn.recv()[0]
                    self.end_pipe.send([data])
                elif message[0] == "z_driver.change_control":
                    self.z_driver_conn.send(["change_control", message[1]])
                elif message[0] == "alpha_driver.ask_control":
                    self.alpha_driver_conn.send(["ask_control"])
                    data = self.alpha_driver_conn.recv()[0]
                    self.end_pipe.send([data])
                elif message[0] == "alpha_driver.change_control":
                    self.alpha_driver_conn.send(["change_control", message[1]])
                elif message[0] == "special_route_x":
                    self.special_command(message[1], message[2], message[3])
                elif message[0] == "special_route_z":
                    self.special_command(message[1], message[2], message[3])
                elif message[0] == "special_route_alpha":
                    self.special_command(message[1], message[2], message[3])
                elif message[0] == "special_route_flow":
                    self.special_command(message[1], message[2], message[3])
                elif message[0] == "change_flute_pos":
                    DATA['flute_position']['X_F'] = message[1]['X_F']
                    DATA['flute_position']['Z_F'] = message[1]['Z_F']
                elif message[0] == "microphone.change_frequency_detection":
                    self.mic_conn.send(["change_frequency_detection", message[1]])
                elif message[0] == "pivot":
                    route_x = message[1]
                    route_z = message[2]
                    route_a = message[3]
                    move_t0 = time.time() - self.t0 + 0.2
                    for i in range(len(route_x)):
                        route_x[i][0] += move_t0
                        route_z[i][0] += move_t0
                        route_a[i][0] += move_t0
                    if self.x_connect:
                        self.x_virtual_axis_conn.send(["merge_ref", route_x])
                    if self.z_connect:
                        self.z_virtual_axis_conn.send(["merge_ref", route_z])
                    if self.alpha_connect:
                        self.alpha_virtual_axis_conn.send(["merge_ref", route_a])
        
        time.sleep(0.5)
        self.mic_running.clear()
        self.comm_event.clear()

    def set_instrument(self, instrument):
        self.instrument = instrument

    def move_to(self, desired_state, T=None, only_x=False, only_z=False, only_alpha=False, only_flow=False, speed=50):
        if only_x:
            x_now = self.x_driver.encoder_position.value
            x_ref = x_mm_to_units(desired_state.x)
            temps, x_points, accel = get_1D_route(x_now, x_ref, speed, acc=4000, dec=4000)
            move_t0 = time.time() - self.t0
            r = []
            for i in range(len(temps)):
                r.append((temps[i] + move_t0, x_points[i], accel[i]))
            self.x_virtual_axis_conn.send(["merge_ref", r])
            return 0
        if only_z:
            z_now = self.z_driver.encoder_position.value
            z_ref = z_mm_to_units(desired_state.z)
            temps, z_points, accel = get_1D_route(z_now, z_ref, speed, acc=4000, dec=4000)
            move_t0 = time.time() - self.t0
            r = []
            for i in range(len(temps)):
                r.append((temps[i] + move_t0, z_points[i], accel[i]))
            self.z_virtual_axis_conn.send(["merge_ref", r])
            return 0
        if only_alpha:
            alpha_now = self.alpha_driver.encoder_position.value
            alpha_ref = alpha_angle_to_units(desired_state.alpha)
            temps, alpha_points, accel = get_1D_route(alpha_now, alpha_ref, speed, acc=4000, dec=4000)
            move_t0 = time.time() - self.t0
            r = []
            for i in range(len(temps)):
                r.append((temps[i] + move_t0, alpha_points[i], accel[i]))
            self.alpha_virtual_axis_conn.send(["merge_ref", r])
            return 0


        my_state = State(0, 0, 0, 0)
        my_state.x = encoder_units_to_mm(self.x_driver.encoder_position.value)
        my_state.z = encoder_units_to_mm(self.z_driver.encoder_position.value)
        my_state.alpha = encoder_units_to_angle(self.alpha_driver.encoder_position.value)
        my_state.flow = self.flow_driver.mass_flow_reading.value
        route = get_route(my_state, desired_state, T=T, acc=50, dec=50, speed=speed/50)

        move_t0 = time.time() - self.t0
        route_x = []
        route_z = []
        route_alpha = []
        route_flow = []
        for i in range(len(route['t'])):
            route_x.append((route['t'][i] + move_t0, route['x'][i], route['x_vel'][i]))
            route_z.append((route['t'][i] + move_t0, route['z'][i], route['z_vel'][i]))
            route_alpha.append((route['t'][i] + move_t0, route['alpha'][i], route['alpha_vel'][i]))
            route_flow.append((route['t'][i] + move_t0, round(route['flow'][i], 2)))
        if self.x_connect and not only_z and not only_alpha and not only_flow:
            self.x_virtual_axis_conn.send(["merge_ref", route_x])
        if self.z_connect and not only_x and not only_alpha and not only_flow:
            self.z_virtual_axis_conn.send(["merge_ref", route_z])
        if self.alpha_connect and not only_x and not only_z and not only_flow:
            self.alpha_virtual_axis_conn.send(["merge_ref", route_alpha])
        if self.flow_connect:
            self.virtual_flow_conn.send(["merge_ref", route_flow, desired_state.vibrato_amp, desired_state.vibrato_freq])

        return route['t'][-1]

    def execute_score(self, path, go_back=True):
        my_state = State(0, 0, 0, 0)
        my_state.x = x_units_to_mm(self.x_driver.encoder_position.value)
        my_state.z = z_units_to_mm(self.z_driver.encoder_position.value)
        my_state.alpha = alpha_units_to_angle(self.alpha_driver.encoder_position.value)
        my_state.flow = self.flow_driver.mass_flow_reading.value

        route = get_route_complete(path, go_back=go_back)
        initial_state = State(0, 0, 0, 0)
        initial_state.x = x_units_to_mm(route['x'][0])
        initial_state.z = z_units_to_mm(route['z'][0])
        initial_state.alpha = alpha_units_to_angle(route['alpha'][0])
        self.move_to(initial_state)

        self.loaded_route_x = []
        self.loaded_route_z = []
        self.loaded_route_alpha = []
        self.loaded_route_flow = []
        self.loaded_route_notes = route['notes']
        for i in range(len(route['t'])):
            self.loaded_route_x.append([route['t'][i], route['x'][i], route['x_vel'][i]])
            self.loaded_route_z.append([route['t'][i], route['z'][i], route['z_vel'][i]])
            self.loaded_route_alpha.append([route['t'][i], route['alpha'][i], route['alpha_vel'][i]])
            self.loaded_route_flow.append([route['t_flow'][i], route['flow'][i]])

    def start_loaded_script(self):
        start_already = True
        if self.x_connect:
            x = self.x_driver.encoder_position.value
            if x - self.loaded_route_x[0][1] > 40:
                start_already = False
        if self.z_connect:
            z = self.z_driver.encoder_position.value
            if z - self.loaded_route_z[0][1] > 40:
                start_already = False
        if self.alpha_connect:
            alpha = self.alpha_driver.encoder_position.value
            if alpha - self.loaded_route_alpha[0][1] > 40:
                start_already = False
        
        if not start_already:
            print('Not quite there yet...')
            return
        else:
            print("Starting...")

        t_start = time.time() - self.t0

        for i in range(len(self.loaded_route_flow)):
            self.loaded_route_x[i][0] += t_start
            self.loaded_route_z[i][0] += t_start
            self.loaded_route_alpha[i][0] += t_start
            self.loaded_route_flow[i][0] += t_start
            self.loaded_route_notes[i][0] += t_start
        print("Starting...")
        if self.x_connect:
            self.x_virtual_axis_conn.send(["merge_ref", self.loaded_route_x])
        if self.z_connect:
            self.z_virtual_axis_conn.send(["merge_ref", self.loaded_route_z])
        if self.alpha_connect:
            self.alpha_virtual_axis_conn.send(["merge_ref", self.loaded_route_alpha])
        if self.flow_connect:
            self.virtual_flow_conn.send(["merge_ref", self.loaded_route_flow, 0, 0])
        if self.fingers_connect:
            self.virtual_fingers_conn.send(["merge_ref", self.loaded_route_notes])

    def stop(self):
        self.x_virtual_axis_conn.send(["stop"])
        self.z_virtual_axis_conn.send(["stop"])
        self.alpha_virtual_axis_conn.send(["stop"])
        self.virtual_flow_conn.send(["stop"])
        self.virtual_fingers_conn.send(["stop"])

    def get_ref_state(self):
        s = State(0,0,0,0)
        s.x = x_units_to_mm(self.x_driver.pos_ref.value)
        s.z = z_units_to_mm(self.z_driver.pos_ref.value)
        s.alpha = alpha_units_to_angle(self.alpha_driver.pos_ref.value)
        s.flow = self.flow_driver.mass_flow_set_point_reading.value
        return s

    def move_to_alpha(self, value):
        self.alpha_driver.homing_move_target = value

    def execute_fingers_action(self, action, through_action=True):
        """
        Ejecuta una acción de los dedos
        """
        if through_action:
            self.fingers_driver.request_finger_action(action['data']['note'])
        else:
            self.fingers_driver.request_finger_action(action)

    def get_instrument(self):
        return self.instrument

    def print_info(self):
        my_state = State(0, 0, 0, 0)
        my_state.x = x_units_to_mm(self.x_driver.motor_position)
        my_state.z = z_units_to_mm(self.z_driver.motor_position)
        my_state.alpha = alpha_units_to_angle(self.alpha_driver.motor_position)
        my_state.flow = self.flow_driver.mass_flow_reading.value
        print(my_state)

class Memory(Process):
    """
    Esta clase se encarga de almacenar la historia de las variables medidas. windowWidth dice la cantidad de datos a almacenar e interval el tiempo (en milisegundos) para obtener una muestra.
    """
    def __init__(self, running, x_driver, z_driver, alpha_driver, flow_controller, pressure_sensor, microphone, pipe_end, data, windowWidth=200, interval=0.05):
        Process.__init__(self) # Initialize the threading superclass
        self.saving = False
        self.x_driver = x_driver
        self.z_driver = z_driver
        self.alpha_driver = alpha_driver
        self.flow_controller = flow_controller
        self.pressure_sensor = pressure_sensor
        self.microphone = microphone
        self.pipe_end = pipe_end
        self.windowWidth = windowWidth
        self.ref_state = State(0,0,0,0)
        self.real_state = State(0,0,0,0)

        self.ref_state.x = x_units_to_mm(self.x_driver.pos_ref.value)
        self.ref_state.z = z_units_to_mm(self.z_driver.pos_ref.value)
        self.ref_state.alpha = alpha_units_to_angle(self.alpha_driver.pos_ref.value)
        self.ref_state.flow = self.flow_controller.mass_flow_set_point_reading.value
        self.real_state.x = x_units_to_mm(self.x_driver.encoder_position.value)
        self.real_state.z = z_units_to_mm(self.z_driver.encoder_position.value)
        self.real_state.alpha = alpha_units_to_angle(self.alpha_driver.encoder_position.value)
        self.real_state.flow = self.flow_controller.mass_flow_reading.value

        self.data = data
        self.data['flow_ref'] = linspace(0,0,200)
        self.data['x_ref'] = linspace(0,0,200)
        self.data['z_ref'] = linspace(0,0,200)
        self.data['alpha_ref'] = linspace(0,0,200)
        self.data['x'] = linspace(0,0,200)
        self.data['z'] = linspace(0,0,200)
        self.data['alpha'] = linspace(0,0,200)
        self.data['radius'] = linspace(0,0,200)
        self.data['theta'] = linspace(0,0,200)
        self.data['offset'] = linspace(0,0,200)
        self.data['radius_ref'] = linspace(0,0,200)
        self.data['theta_ref'] = linspace(0,0,200)
        self.data['offset_ref'] = linspace(0,0,200)
        self.data['mouth_pressure'] = linspace(0,0,200)
        self.data['volume_flow'] = linspace(0,0,200)
        self.data['mass_flow'] = linspace(0,0,200)
        self.data['temperature'] = linspace(0,0,200)
        self.data['frequency'] = linspace(0,0,200)
        self.data['times'] = linspace(0,0,200)
        
        self.t0 = time.time()
        self.first_entry = False
        self.t1 = 0

        self.data_frame = pd.DataFrame(columns=['times','frequency','temperature','mass_flow', 'volume_flow', 'mouth_pressure', 'offset', 'theta', 'radius', 'offset_ref', 'theta_ref', 'radius_ref', 'alpha', 'z', 'x', 'alpha_ref', 'z_ref', 'x_ref', 'flow_ref'])

        self.interval = interval
        self.running = running

    def run(self):
        self.pipe_end.send(["memory_started"])
        while self.running.is_set():
            
            self.ref_state.x = x_units_to_mm(self.x_driver.pos_ref.value)
            self.ref_state.z = z_units_to_mm(self.z_driver.pos_ref.value)
            self.ref_state.alpha = alpha_units_to_angle(self.alpha_driver.pos_ref.value)
            self.ref_state.flow = self.flow_controller.mass_flow_set_point_reading.value
            self.real_state.x = encoder_units_to_mm(self.x_driver.encoder_position.value)
            self.real_state.z = z_units_to_mm(self.z_driver.encoder_position.value)
            self.real_state.alpha = alpha_units_to_angle(self.alpha_driver.encoder_position.value)
            self.real_state.flow = self.flow_controller.mass_flow_reading.value

            
            self.data['x_ref'] = np.hstack([self.data['x_ref'][1:], self.ref_state.x])
            self.data['z_ref'] = np.hstack([self.data['z_ref'][1:], self.ref_state.z])
            self.data['alpha_ref'] = np.hstack([self.data['alpha_ref'][1:], self.ref_state.alpha])
            self.data['flow_ref'] = np.hstack([self.data['flow_ref'][1:], self.flow_controller.mass_flow_set_point_reading.value])
            self.data['x'] = np.hstack([self.data['x'][1:], self.real_state.x])
            self.data['z'] = np.hstack([self.data['z'][1:], self.real_state.z])
            self.data['alpha'] = np.hstack([self.data['alpha'][1:], self.real_state.alpha])
            self.data['volume_flow'] = np.hstack([self.data['volume_flow'][1:], self.flow_controller.vol_flow_reading.value])

            self.data['radius'] = np.hstack([self.data['radius'][1:], self.real_state.r])
            self.data['theta'] = np.hstack([self.data['theta'][1:], self.real_state.theta])
            self.data['offset'] = np.hstack([self.data['offset'][1:], self.real_state.o])
            self.data['radius_ref'] = np.hstack([self.data['radius_ref'][1:], self.ref_state.r])
            self.data['theta_ref'] = np.hstack([self.data['theta_ref'][1:], self.ref_state.theta])
            self.data['offset_ref'] = np.hstack([self.data['offset_ref'][1:], self.ref_state.o])
            self.data['mouth_pressure'] = np.hstack([self.data['mouth_pressure'][1:], self.pressure_sensor.pressure.value])
            self.data['mass_flow'] = np.hstack([self.data['mass_flow'][1:], self.flow_controller.mass_flow_reading.value])
            self.data['temperature'] = np.hstack([self.data['temperature'][1:], self.flow_controller.temperature_reading.value])
            self.data['frequency'] = np.hstack([self.data['frequency'][1:], self.microphone.pitch.value])
            self.data['times'] = np.hstack([self.data['times'][1:], time.time() - self.t0])  
            if self.saving:
                if self.first_entry:
                    self.t1 = self.data['times'][-1]
                    self.first_entry = False

                new_data = pd.DataFrame([[self.data['times'][-1] - self.t1, self.data['frequency'][-1], self.data["temperature"][-1], self.data["mass_flow"][-1], self.data["volume_flow"][-1], self.data["mouth_pressure"][-1], self.data["offset"][-1], self.data["theta"][-1], self.data["radius"][-1], self.data["offset_ref"][-1], self.data["theta_ref"][-1], self.data["radius_ref"][-1], self.data["alpha"][-1], self.data["z"][-1], self.data["x"][-1], self.data["alpha_ref"][-1], self.data["z_ref"][-1], self.data["x_ref"][-1], self.data["flow_ref"][-1]]], columns=['times','frequency','temperature','mass_flow', 'volume_flow', 'mouth_pressure', 'offset', 'theta', 'radius', 'offset_ref', 'theta_ref', 'radius_ref', 'alpha', 'z', 'x', 'alpha_ref', 'z_ref', 'x_ref', 'flow_ref'])
                self.data_frame = pd.concat([self.data_frame, new_data], ignore_index=True)
            
            if self.pipe_end.poll(self.interval):
                message = self.pipe_end.recv()
                print("Message received in memory:", message[0])
                if message[0] == "get_data":
                    self.pipe_end.send([self.data])
                if message[0] == "start_saving":
                    self.start_saving()
                if message[0] == "stop_recording":
                    self.stop_recording()
                if message[0] == "save_recorded_data":
                    self.save_recorded_data(message[1])
                    print("Data saved to file", message[1])
    
    def start_saving(self):
        self.first_entry = True
        self.data_frame = pd.DataFrame(columns=['times','frequency','temperature','mass_flow', 'volume_flow', 'mouth_pressure', 'offset', 'theta', 'radius', 'alpha', 'z', 'x', 'alpha_ref', 'z_ref', 'x_ref', 'flow_ref'])
        self.saving = True
    
    def pause_saving(self):
        self.saving = False

    def resume_saving(self):
        self.saving = True
    
    def finish_saving(self, file_name):
        self.saving = False
        self.data_frame.to_csv(file_name)

    def save_recorded_data(self, filename1):
        self.finish_saving(filename1)

    def stop_recording(self):
        self.saving = False