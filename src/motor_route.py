import sys
sys.path.insert(0, 'C:/Users/ferna/Dropbox/UC/Magister/robot-flautista')
import matplotlib.pyplot as plt
from src.cinematica import *
import json
from scipy import signal
import csv

def get_route_positions(xi, zi, alphai, xf, zf, alphaf, divisions=20, plot=False, aprox=True):
    ri, thetai, oi = get_l_theta_of(xi, zi, alphai)
    rf, thetaf, of = get_l_theta_of(xf, zf, alphaf)

    deltaR = rf - ri
    deltaTheta = thetaf - thetai
    deltaO = of - oi

    x2i, z2i = get_pos_punta(xi, zi, alphai*pi/180)
    x_a, z_a, alpha_a = xi, zi, alphai

    x2f, z2f = get_pos_punta(xf, zf, alphaf*pi/180)

    dist = 0
    d = []
    x_points = []
    z_points = []
    alpha_points = []
    x2_points = []
    z2_points = []
    for n in range(divisions+1):
        xn, zn, alphan = get_x_z_alpha(ri + n*deltaR/divisions, thetai + n*deltaTheta/divisions, oi + n*deltaO/divisions)
        #print(ri + n*deltaR/N, thetai + n*deltaTheta/N, oi + n*deltaO/N)
        #print(get_r_theta_o(xn, zn, alphan))
        #print(alphan)
        x_points.append(round(xn,3))
        z_points.append(round(zn,3))
        alpha_points.append(round(alphan,3))
        if plot:
            x2, z2 = get_pos_punta(xn, zn, alphan*pi/180)
            x2_points.append(x2)
            z2_points.append(z2)
        dist += sqrt((xn - x_a)**2 + (zn - z_a)**2 + (alphan - alpha_a)**2)
        d.append(dist)
        x_a, z_a, alpha_a = xn, zn, alphan

    return x_points, z_points, alpha_points, d

def max_dist_rec(acc, dec, T):
    d_acc = (acc/2) * ((dec*T)/(acc+dec))**2
    d_dec = acc*(dec*T)/(acc+dec) * (T-(dec*T)/(acc+dec)) / 2
    dist_max = d_acc + d_dec
    return dist_max

def plan_speed_curve(d, acceleration, deceleration, T):
    #print(acceleration*deceleration*(acceleration*deceleration*T**2 - 2*acceleration*d - 2*deceleration*d))
    speed = (acceleration*deceleration*T - sqrt(acceleration*deceleration*(acceleration*deceleration*T**2 - 2*acceleration*d - 2*deceleration*d))) / (acceleration+deceleration)
    t_acc = speed / acceleration
    t_dec = T - speed / deceleration
    return speed, t_acc, t_dec

def plan_temps_according_to_speed(distances, vel, t_acc, t_dec, acc, dec):
    d_t_acc = acc * t_acc**2 / 2
    d_t_dec = d_t_acc + vel * (t_dec - t_acc)
    temps = []
    for d_sum in distances:
        if d_sum < d_t_acc:
            temps.append(sqrt(2*d_sum/acc))
        elif d_sum < d_t_dec:
            temps.append((d_sum - d_t_acc)/vel + t_acc)
        else:
            a = dec / 2
            b = -(vel + (2*t_dec*dec)/2)
            c = d_sum - d_t_dec + vel*t_dec + (dec*t_dec**2)/2
            #print(round(b**2 - 4*a*c, 3))
            t = (-b - sqrt(round(b**2 - 4*a*c,3)))/(2*a)
            temps.append(t)
    return temps

def x_mm_to_units(mm, aprox=True):
    if aprox:
        return int(mm * 4000 / 8 )
    else:
        return mm * 4000 / 8

def x_units_to_mm(units):
    return units * 8 / 4000

def encoder_units_to_mm(units):
    return units * 8 / 4000

def encoder_units_to_angle(units):
    return units * 360 / 4000
    
def z_mm_to_units(mm, aprox=True):
    if aprox:
        return int(mm * 4000 / 8 )
    else:
        return mm * 4000 / 8

def z_units_to_mm(units):
    return units * 8 / 4000
    
def alpha_angle_to_units(angle, aprox=True):
    if aprox:
        return int(angle * 4000 / 360)
    else:
        return angle * 4000 / 360

def alpha_units_to_angle(units):
    return units * 360 / 4000
    
def plan_route(x_points, z_points, alpha_points, temps, aprox=True):
    points = {'x': [], 'z': [], 'alpha': [], 't': []}

    for i in range(len(x_points) - 1):
        x = x_mm_to_units(x_points[i], aprox=aprox)            
        z = z_mm_to_units(z_points[i], aprox=aprox)
        alpha = alpha_angle_to_units(alpha_points[i], aprox=aprox)
        t = temps[i]

        points['x'].append(x)
        points['z'].append(z)
        points['alpha'].append(alpha)
        points['t'].append(t)

    return points
        
def get_route_a_b(initial_state, final_state, acc=20, dec=20, T=None, divisions=12, aprox=True):
    x_points, z_points, alpha_points, d = get_route_positions(*initial_state.cart_coords(), *final_state.cart_coords(), divisions=divisions, plot=False)
    if not T:
        T = 0.1
        while True:
            if not max_dist_rec(acc, dec, T) < d[-1]:
                break
            T += 0.1
        T = T*2
    else:
        if max_dist_rec(acc, dec, T) < d[-1]:
            print(f'Impossible to achieve such position with given acceleration and deceleration. {d[-1]} > {max_dist_rec(acc, dec, T)}')
            #print(1, acc, dec)
            return None
    vel, t_acc, t_dec = plan_speed_curve(d[-1], acc, dec, T)
    temps = plan_temps_according_to_speed(d, vel, t_acc, t_dec, acc, dec)
    route = plan_route(x_points, z_points, alpha_points, temps, aprox=aprox)
    route['x'].append(x_mm_to_units(final_state.x, aprox=aprox))
    route['z'].append(z_mm_to_units(final_state.z, aprox=aprox))
    route['alpha'].append(alpha_angle_to_units(final_state.alpha, aprox=aprox))
    route['t'].append(T)
    return route

def get_min_T(d, acc, dec, v_max=4000):
    dist_1 = v_max**2 / (2*acc) + v_max**2 / (2*dec)
    if dist_1 < d:
        dif = d - dist_1
        return v_max / acc + v_max / dec + dif / v_max
    else:
        v_2 = sqrt(2*acc*dec*d/(acc+dec))
        #print('dist', dist_1, d, v_2)
        return v_2 / acc + v_2 / dec

def get_1D_route(initial_p, final_p, speed, acc=20, dec=20):
    d = abs(final_p - initial_p)
    if d == 0:
        return []
    min_T = get_min_T(d, acc, dec)
    #print(min_T)
    T = min_T * (100/speed)
    vel, t_acc, t_dec = plan_speed_curve(d, acc, dec, T)
    #print(vel, t_acc, t_dec)
    x_points = linspace(initial_p, final_p, int(T*200))
    temps = plan_temps_according_to_speed(abs(x_points - initial_p), vel, t_acc, t_dec, acc, dec)

    accel = []
    for i in range(len(temps) - 1):
        dT = (temps[i + 1] - temps[i])
        if dT == 0:
            accel.append(0)
        else:
            accel.append(int((x_points[i + 1] - x_points[i]) / dT))
    accel.append(0)
    
    return temps, x_points, accel
    

def get_route(initial_state, final_state, acc=20, dec=20, T=None, divisions=100, aprox=False, speed=1):
    x_points, z_points, alpha_points, d = get_route_positions(*initial_state.cart_coords(), *final_state.cart_coords(), divisions=divisions, plot=False)
    if not T:
        T = 0.1
        while True:
            if not max_dist_rec(acc, dec, T) < d[-1]:
                break
            T += 0.1
        T = T*2/speed
    else:
        if max_dist_rec(acc, dec, T) < d[-1]:
            print(f'Impossible to achieve such position with given acceleration and deceleration. {d[-1]} > {max_dist_rec(acc, dec, T)}')
            #print(2, acc, dec)
            return None
    x_points, z_points, alpha_points, d = get_route_positions(*initial_state.cart_coords(), *final_state.cart_coords(), divisions=int(divisions*T), plot=False)
    vel, t_acc, t_dec = plan_speed_curve(d[-1], acc, dec, T)
    temps = plan_temps_according_to_speed(d, vel, t_acc, t_dec, acc, dec)
    route = plan_route(x_points, z_points, alpha_points, temps, aprox=aprox)
    route['x'].append(x_mm_to_units(final_state.x, aprox=aprox))
    route['z'].append(z_mm_to_units(final_state.z, aprox=aprox))
    route['alpha'].append(alpha_angle_to_units(final_state.alpha, aprox=aprox))
    route['t'].append(T)

    route['x_vel'] = [0, 0]
    route['z_vel'] = [0, 0]
    route['alpha_vel'] = [0, 0]
    
    for i in range(len(route['t']) - 1):
        dT = (route['t'][i + 1] - route['t'][i])
        if dT == 0:
            route['x_vel'].append(0)
            route['z_vel'].append(0)
            route['alpha_vel'].append(0)
        else:
            route['x_vel'].append(int((route['x'][i + 1] - route['x'][i]) / dT))
            #print(dT, route['x_vel'][-1], route['x'][i + 1] - route['x'][i], route['x'][i])
            route['z_vel'].append(int((route['z'][i + 1] - route['z'][i]) / dT))
            route['alpha_vel'].append(int((route['alpha'][i + 1] - route['alpha'][i]) / dT))
    route['x_vel'].append(0)
    route['z_vel'].append(0)
    route['alpha_vel'].append(0)

    route['x'] = list(map(lambda x: round(x), route['x']))
    route['z'] = list(map(lambda x: round(x), route['z']))
    route['alpha'] = list(map(lambda x: round(x), route['alpha']))

    route['x_vel'] = list(map(lambda x: round(x), route['x_vel'][2:]))
    route['z_vel'] = list(map(lambda x: round(x), route['z_vel'][2:]))
    route['alpha_vel'] = list(map(lambda x: round(x), route['alpha_vel'][2:]))

    Fi = initial_state.flow
    Ff = final_state.flow
    deformation = 1
    route['flow'] = []

    for i in range(len(route['t'])):
        t = route['t'][i]
        ramp = Fi + (Ff-Fi) * (t / T) ** deformation
        flow_sat = max(0,min(50, ramp))
        route['flow'].append(flow_sat)
        
    return route

def get_route_complete(path, go_back=True):
    with open(path) as file:
        data = json.load(file)
    
    #state_at_begining = State(*get_r_theta_o(x,z,alpha), 0)
    initial_state = State(data['init_pos']['r'], data['init_pos']['theta'], data['init_pos']['offset'], 0)

    route = {'x': [x_mm_to_units(initial_state.x)],
             'z': [z_mm_to_units(initial_state.z)],
             'alpha': [alpha_angle_to_units(initial_state.alpha)],
             'flow': [0],
             't': [0],
             't_flow': [0]} #get_route_a_b(state_at_begining, initial_state, acc=20, dec=20, T=None, divisions=200)

    for act in data['phrase']:
        if act['move']:
            x = x_units_to_mm(route['x'][-1])
            z = z_units_to_mm(route['z'][-1])
            alpha = alpha_units_to_angle(route['alpha'][-1])
            a = State(*get_l_theta_of(x, z, alpha), 0)
            b = State(act['r'], act['theta'], act['offset'], act['flow'])
            route_add = get_route_a_b(a, b, acc=act['acceleration'], dec=act['deceleration'], T=act['time'], divisions=int(act['time']*100), aprox=False)
            #print(route_add['x'])
            route_add['t_flow'] = []

            Fi = route['flow'][-1]
            Ff = act['flow']
            t  = route['t'][-1]
            ti = t
            T  = act['time']
            deformation = act['deformation']
            vibrato_amp = act['vibrato_amp']
            vibrato_freq = act['vibrato_freq']

            for i in range(len(route_add['t'])):
                route_add['t'][i] = route_add['t'][i] + ti
                ramp = Fi + (Ff-Fi) * ((t-ti) / T) ** deformation
                vibr = ramp * vibrato_amp * sin(t * 2*pi * vibrato_freq)
                flow_sat = max(0,min(50, ramp+vibr))
                route['flow'].append(flow_sat)
                route_add['t_flow'].append(t)
                t += 0.01


            route['x'] += route_add['x']
            route['z'] += route_add['z']
            route['alpha'] += route_add['alpha']
            route['t'] += route_add['t']
            route['t_flow'] += route_add['t_flow']
        else:
            t = route['t'][-1]
            T  = act['time']
            Fi = act['flow']
            vibrato_amp = act['vibrato_amp']
            vibrato_freq = act['vibrato_freq']
            for i in range(int(T*100)):
                t += 0.01
                vibr = Fi * vibrato_amp * sin(t * 2*pi * vibrato_freq)
                flow_sat = max(0,min(50, Fi+vibr))
                route['flow'].append(flow_sat)
                route['x'].append(route['x'][-1])
                route['z'].append(route['z'][-1])
                route['alpha'].append(route['alpha'][-1])
                route['t'].append(t)
                route['t_flow'].append(t)

    x = x_units_to_mm(route['x'][-1])
    z = z_units_to_mm(route['z'][-1])
    alpha = alpha_units_to_angle(route['alpha'][-1])
    a = State(*get_l_theta_of(x, z, alpha), 0)
    b = State(initial_state.r, initial_state.theta, initial_state.o, 0)
    route_add = get_route_a_b(a, b, acc=99, dec=99, T=2, divisions=int(2*100), aprox=False)
    route_add['t_flow'] = []

    Fi = route['flow'][-1]
    Ff = 0
    t  = route['t'][-1]
    ti = t
    T  = 1
    deformation = 1
    vibrato_amp = 0
    vibrato_freq = 0

    for i in range(len(route_add['t'])):
        route_add['t'][i] = route_add['t'][i] + ti
        ramp = Fi + (Ff-Fi) * ((t-ti) / T) ** deformation
        vibr = ramp * vibrato_amp * sin(t * 2*pi * vibrato_freq)
        flow_sat = max(0,min(50, ramp+vibr))
        route['flow'].append(flow_sat)
        route_add['t_flow'].append(t)
        t += 0.01

    if go_back:
        route['x'] += route_add['x']
        route['z'] += route_add['z']
        route['alpha'] += route_add['alpha']
        route['t'] += route_add['t']   
        route['t_flow'] += route_add['t_flow']
    
    
    route['x_vel'] = []
    route['z_vel'] = []
    route['alpha_vel'] = []
    
    for i in range(len(route['t']) - 1):
        dT = (route['t'][i + 1] - route['t'][i])
        if dT == 0:
            route['x_vel'].append(0)
            route['z_vel'].append(0)
            route['alpha_vel'].append(0)
        else:
            route['x_vel'].append(int((route['x'][i + 1] - route['x'][i]) / dT))
            #print(dT, route['x_vel'][-1], route['x'][i + 1] - route['x'][i], route['x'][i])
            route['z_vel'].append(int((route['z'][i + 1] - route['z'][i]) / dT))
            route['alpha_vel'].append(int((route['alpha'][i + 1] - route['alpha'][i]) / dT))
    route['x_vel'].append(0)
    route['z_vel'].append(0)
    route['alpha_vel'].append(0)

    route['x'] = list(map(lambda x: round(x), route['x']))
    route['z'] = list(map(lambda x: round(x), route['z']))
    route['alpha'] = list(map(lambda x: round(x), route['alpha']))

    route['x_vel'] = list(map(lambda x: round(x), route['x_vel']))
    route['z_vel'] = list(map(lambda x: round(x), route['z_vel']))
    route['alpha_vel'] = list(map(lambda x: round(x), route['alpha_vel']))

    t = 0
    route['notes'] = []
    for note in data['fingers']:
        t += note['time']
        route['notes'].append((t, note['note']))
        
    return route

def get_value_from_func(t, func, approx=True):
    t_val = min(int((len(func) - 1) * t / max(func[-1][0], 0.000001)), len(func) - 1)
    if t < func[t_val][0]:
        while t < func[t_val][0]:
            t_val -= 1
            if t_val < 0:
                if approx:
                    return round(func[0][1])
                else:
                    return func[0][1]
        r = func[t_val][1] + ((t - func[t_val][0]) / (func[t_val + 1][0] - func[t_val][0])) * (func[t_val + 1][1] - func[t_val][1])
        if approx:
            return round(r)
        else:
            return r
    else:
        while t > func[t_val][0]:
            t_val += 1
            if t_val >= len(func):
                if approx:
                    return round(func[-1][1])
                else:
                    return func[-1][1]
        r = func[t_val - 1][1] + ((t - func[t_val - 1][0]) / (func[t_val][0] - func[t_val - 1][0])) * (func[t_val][1] - func[t_val - 1][1])
        if approx:
            return round(r)
        else:
            return r

def get_value_from_func_2d(t, func):
    t_val = min(int((len(func) - 1) * t / max(0.000001, func[-1][0])), len(func) - 1)
    if t < func[t_val][0]:
        while t < func[t_val][0]:
            t_val -= 1
            if t_val < 0:
                return func[0][1], func[0][2]
        return round(func[t_val][1] + ((t - func[t_val][0]) / (func[t_val + 1][0] - func[t_val][0])) * (func[t_val + 1][1] - func[t_val][1])), round(func[t_val][2] + ((t - func[t_val][0]) / (func[t_val + 1][0] - func[t_val][0])) * (func[t_val + 1][2] - func[t_val][2]))
    else:
        while t > func[t_val][0]:
            t_val += 1
            if t_val >= len(func):
                return func[-1][1], func[-1][2]
        return round(func[t_val - 1][1] + ((t - func[t_val - 1][0]) / (func[t_val][0] - func[t_val - 1][0])) * (func[t_val][1] - func[t_val - 1][1])), round(func[t_val - 1][2] + ((t - func[t_val - 1][0]) / (func[t_val][0] - func[t_val - 1][0])) * (func[t_val][2] - func[t_val - 1][2]))


def third_order_time_scale(t, T):
    a0 = 0
    a1 = 0
    a2 = 3 / (T**2)
    a3 = -2 / (T**3)
    return a0 + a1*t + a2*t**2 + a3*t**3

def third_order_time_scale_speed(t, T):
    a1 = 0
    a2 = 3 / (T**2)
    a3 = -2 / (T**3)
    return a1 + 2*a2*t + 3*a3*t**2

# def time_scaled_straight_line(x_i, z_i, alpha_i, x_f, z_f, alpha_f, T):
#     r = {'x': [],
#          'z': [],
#          'alpha': []}
#     for i in range(int(T*100) + 1):
#         s = third_order_time_scale(i * T / int(T*100), T)
#         sp = third_order_time_scale_speed(i * T / int(T*100), T)
#         r['x'].append([s*T, int(round(x_i + s*(x_f - x_i), 0)), int(round(sp*(x_f - x_i)/T, 0))])
#         r['z'].append([s*T, int(round(z_i + s*(z_f - z_i), 0)), int(round(sp*(z_f - z_i)/T, 0))])
#         r['alpha'].append([s*T, int(round(alpha_i + s*(alpha_f - alpha_i), 0)), int(round(sp*(alpha_f - alpha_i)/T, 0))])
#     return r

def time_scaled_straight_line(route, T):
    r = {'x': [],
         'z': [],
         'alpha': []}
    vel_route = gradient(route)
    for i in range(len(route) + 1):
        s = third_order_time_scale(i * T / len(route), T)
        sp = third_order_time_scale_speed(i * T / len(route), T)
        r['x'].append([s*T, route[int(s*(len(route)-1))][0], int(round(sp*vel_route[0][int(s*(len(route)-1))][0]*len(route)/T,0))])
        r['z'].append([s*T, route[int(s*(len(route)-1))][1], int(round(sp*vel_route[0][int(s*(len(route)-1))][1]*len(route)/T,0))])
        r['alpha'].append([s*T, route[int(s*(len(route)-1))][2], int(round(sp*vel_route[0][int(s*(len(route)-1))][2]*len(route)/T,0))])
    return r


if __name__ == '__main__':
    x_i = x_mm_to_units(19.976)
    z_i = z_mm_to_units(20.034)
    alpha_i = alpha_angle_to_units(0.09)
    x_f = x_mm_to_units(20.82116192497326)
    z_f = z_mm_to_units(10.545442961167977)
    alpha_f = alpha_angle_to_units(10.09)
    T = 2.0
    r = time_scaled_straight_line(x_i, z_i, alpha_i, x_f, z_f, alpha_f, T)
    print(r['x'])
    # path = '/home/fernando/Dropbox/UC/Magister/robot-flautista/examples/escala_1.json'
    # r = get_route_complete(path)

    # r, temps, x_points = get_1D_route(0, x_mm_to_units(0.5), 50, acc=400, dec=400)
    # r, temps, x_points = get_1D_route(x_mm_to_units(0.5), x_mm_to_units(1), 50, acc=400, dec=400)
    # r, temps, x_points = get_1D_route(x_mm_to_units(1), x_mm_to_units(0.5), 50, acc=400, dec=400)
    #print(r)
    #plt.plot(r['t'], r['x'])
    # plt.plot(temps, x_points)
    # plt.ylabel('some numbers')
    # plt.show()