import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal

def get_new_route(t_total, Fs):
    return np.zeros([int(t_total*Fs)])

def get_rampa(t_init, t_change, delta_v, t_total, Fs=100):
    return np.pad(np.linspace(0, delta_v, int(round(t_change*Fs, 0))),(int(round(t_init*Fs, 0)), int(round(t_total*Fs,0))-int(round(t_init*Fs,0))-int(round(t_change*Fs, 0))), 'constant', constant_values=(0,delta_v))

def get_route_ramped(points, t_max, Fs=100):
    ramped = np.zeros([int(t_max*Fs)])
    if len(points):
        ramped += points[0][1]
    for i in range(len(points) - 1):
        ramped += get_rampa(points[i][0], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1], t_max)
    return ramped

ventanas = {'rect': np.ones, 'triangular': np.bartlett, 'blackman': np.blackman, 'hamming': np.hamming, 'hanning': np.hanning, 'kaiser1': lambda x: np.kaiser(x, 1), 'kaiser2': lambda x: np.kaiser(x, 2), 'kaiser3': lambda x: np.kaiser(x, 3), 'kaiser4': lambda x: np.kaiser(x, 4), 'ramp': lambda x: np.linspace(0, 1, x)}

def sum_vibrato(func, t_inicio, t_vibrato, amp, freq, ventana, t_max, Fs=100):
    ventana = ventanas[ventana]
    t = np.linspace(0, t_max, int(round(t_max*Fs, 0)))
    return func + np.pad(ventana(int(round(t_vibrato*Fs, 0))), (int(round(t_inicio*Fs)),int(round(t_max*Fs-t_vibrato*Fs-t_inicio*Fs, 0)))) * amp * np.sin(freq*np.pi*t)

## hamming
def hamming_filter(f, numtaps, cutoff, Fs):
    flt = signal.firwin(numtaps=numtaps, cutoff=cutoff, window="hamming", pass_zero="lowpass", fs=Fs)
    A = [1] +  [0 for i in range(numtaps-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## hann
def hann_filter(f, numtaps, cutoff, Fs):
    flt = signal.firwin(numtaps=numtaps, cutoff=cutoff, window="hann", pass_zero="lowpass", fs=Fs)
    A = [1] +  [0 for i in range(numtaps-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## blackman
def blackman_filter(f, numtaps, cutoff, Fs):
    flt = signal.firwin(numtaps=numtaps, cutoff=cutoff, window="blackman", pass_zero="lowpass", fs=Fs)
    A = [1] +  [0 for i in range(numtaps-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## bartlett
def bartlett_filter(f, numtaps, cutoff, Fs):
    flt = signal.firwin(numtaps=numtaps, cutoff=cutoff, window="bartlett", pass_zero="lowpass", fs=Fs)
    A = [1] +  [0 for i in range(numtaps-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## rect
def rect_filter(f, numtaps, cutoff, Fs):
    flt = signal.firwin(numtaps=numtaps, cutoff=cutoff, window="boxcar", pass_zero="lowpass", fs=Fs)
    A = [1] +  [0 for i in range(numtaps-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

def remez_filter(f, Ap, As, fp, fs, Fs):
    delta_p = (10**(Ap/20)-1)/(10**(Ap/20)+1)
    delta_s = (1+delta_p)/(10**(As/20))
    n = int(np.ceil((-20*np.log10(np.sqrt(delta_p*delta_s))-13)/(2.324*((fs-fp)/Fs)*2*np.pi)+1))
    if not n%2:
        n+=1
    print(n)
    flt = signal.remez(n, [0, fp, fs, 0.5*Fs], [1, 0], fs=Fs)
    A = [1] +  [0 for i in range(n-1)]
    w, gd = signal.group_delay((flt, A), fs=Fs)
    return signal.lfilter(flt, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

def butter_filter(f, Ap, As, fp, fs, Fs):
    N, Wn = signal.buttord(fp, fs, Ap, As, fs=Fs)
    B, A = signal.butter(N, Wn, btype='low', fs=Fs)
    w, gd = signal.group_delay((B, A), fs=Fs)
    return signal.lfilter(B, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## cheb1
def cheb1_filter(f, Ap, As, fp, fs, rp, Fs):
    n, wn = signal.cheb1ord(fp, fs, Ap, As, fs=Fs)
    B, A  = signal.cheby1(n, rp, wn, 'low', fs=Fs)
    w, gd = signal.group_delay((B, A), fs=Fs)
    return signal.lfilter(B, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## cheb2
def cheb2_filter(f, Ap, As, fp, fs, rp, Fs):
    n, wn = signal.cheb2ord(fp, fs, Ap, As, fs=Fs)
    B, A  = signal.cheby2(n, rp, wn, 'low', fs=Fs)
    w, gd = signal.group_delay((B, A), fs=Fs)
    return signal.lfilter(B, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

## elliptic
def ellip_filter(f, Ap, As, fp, fs, Fs):
    n, wn = signal.ellipord(fp, fs, Ap, As, fs=Fs)
    B, A  = signal.ellip(n, Ap, As, wn, 'low', fs=Fs)
    w, gd = signal.group_delay((B, A), fs=Fs)
    return signal.lfilter(B, A, np.pad(f, (int(gd[0]), int(gd[0])), 'constant', constant_values=(f[0], f[-1])))[int(2*int(gd[0])):]

def filter_func(f, filter, params, Fs):
    if filter == "firwin":
        '''
        params = [window, n, cutoff]
        '''
        window = params[0]
        n = params[1]
        cutoff = params[2]
        if window == "hamming":
            return hamming_filter(f, n, cutoff, Fs)
        elif window == "hann":
            return hann_filter(f, n, cutoff, Fs)
        elif window == "blackman":
            return blackman_filter(f, n, cutoff, Fs)
        elif window == "bartlett":
            return bartlett_filter(f, n, cutoff, Fs)
        elif window == "rect":
            return rect_filter(f, n, cutoff, Fs)
        else:
            raise Exception("Parameters for filter not valid")
    elif filter == "remez":
        """ 
        params = [Ap, As, fp, fs]
        """
        Ap = params[0]
        As = params[1]
        fp = params[2]
        fs = params[3]
        return remez_filter(f, Ap, As, fp, fs, Fs)
    elif filter == "butter":
        """ 
        params = [Ap, As, fp, fs]
        """
        Ap = params[0]
        As = params[1]
        fp = params[2]
        fs = params[3]
        return butter_filter(f, Ap, As, fp, fs, Fs)
    elif filter == "chebyshev":
        """ 
        params = [n, Ap, As, fp, fs, rp]
        """
        n  = params[0]
        Ap = params[1]
        As = params[2]
        fp = params[3]
        fs = params[4]
        rp = params[5]
        if n == 1:
            return cheb1_filter(f, Ap, As, fp, fs, rp, Fs)
        elif n == 2:
            return cheb2_filter(f, Ap, As, fp, fs, rp, Fs)
    elif filter == "elliptic":
        """ 
        params = [Ap, As, fp, fs]
        """
        Ap = params[0]
        As = params[1]
        fp = params[2]
        fs = params[3]
        return ellip_filter(f, Ap, As, fp, fs, Fs)
    else:
        raise Exception("Filter not implemented, try with firwin, remez, butter, chebyshev or elliptic")
    
def filter_part_func(f, i_init, i_end, filter, params, Fs):
    f_sub = f[int(round(i_init*Fs, 0)):int(round(i_end*Fs, 0))]
    filtered = filter_func(f_sub, filter, params, Fs)
    f[int(round(i_init*Fs, 0)):int(round(i_end*Fs, 0))] = filtered
    return f

def lengthen_func(f, new_t_max, Fs):
    return np.linspace(0, new_t_max, int(round(new_t_max*Fs, 0))), np.hstack([f, f[-1]*np.ones([int(round(new_t_max*Fs, 0))-len(f)])])

def shorten_func(f, new_t_max, Fs):
    return np.linspace(0, new_t_max, int(round(new_t_max*Fs, 0))), f[:int(round(new_t_max*Fs, 0))]

def change_duration(f, new_t_max, Fs):
    if new_t_max > len(f)*Fs:
        return lengthen_func(f, new_t_max, Fs)
    else:
        return shorten_func(f, new_t_max, Fs)
    
""" 
Una ruta se define con 5 atributos:
ruta = {
    'total_t': tiempo total de la señal
    'Fs'     : frecuencia del muestreo
    'points' : lista de puntos
    'filters': lista de filtros que se aplican
    'vibrato': lista de vibratos que se aplican
    'history': historial de operaciones que se realizan
}

Tipos de operaciones:
- new_route, [t_max, Fs]
- add_point, [t, value]
- delete_point, [t, value]
- vibrato, [t_inicio, t_vibrato, amp, freq, ventana]
- delete_vibrato, [t_inicio, t_vibrato, amp, freq, ventana]
- filter, [i_init, i_end, filter, params]
- delete_filter, [i_init, i_end, filter, params]
- change_duration, [new_t_max]
"""
def calculate_route(route):
    t_total = route['total_t']
    Fs = route['Fs']
    points = route['points']
    vibratos = route['vibrato']
    filters = route['filters']
    f = get_new_route(t_total, Fs)
    f = get_route_ramped(points, t_total, Fs=Fs)
    fil_t = []
    for filt in filters:
        i_init = filt[0]
        i_end = filt[1]
        filter = filt[2]
        params = filt[3]
        fil_t.append(i_init)
        f = filter_part_func(f, i_init, i_end, filter, params, Fs)
    vib_t = []
    for vib in vibratos:
        t_init = vib[0]
        t_vibrato = vib[1]
        amp = vib[2]
        freq = vib[3]
        window = vib[4]
        vib_t.append(t_init)
        f = sum_vibrato(f, t_init, t_vibrato, amp, freq, window, t_total, Fs=Fs)
    t = np.linspace(0, t_total, int(round(t_total*Fs, 0)))
    return t, f, points, vib_t, fil_t

dict_notes = {0.0: 'D3', 0.5: 'D#3', 1.0: 'E3', 1.5: 'F3', 2.0: 'F#3', 2.5: 'G3', 3.0: 'G#3', 3.5: 'A3', 4.0: 'A#3', 4.5: 'B3', 5.0: 'C4', 5.5: 'C#4', 6.0: 'D4', 6.5: 'D#4', 7.0: 'E4', 7.5: 'F4', 8.0: 'F#4', 8.5: 'G4', 9.0: 'G#4', 9.5: 'A4', 10.0: 'A#4', 10.5: 'B4', 11.0: 'C5', 11.5: 'C#5', 12.0: 'D5', 12.5: 'D#5', 13.0: 'E5', 13.5: 'F5', 14.0: 'F#5', 14.5: 'G5', 15.0: 'G#5', 15.5: 'A5', 17.0: 'C6'}
dict_notes_rev = {}
for key, item in dict_notes.items():
    dict_notes_rev[item] = key

def calculate_notes_route(route):
    t_total = route['total_t']
    Fs = route['Fs']
    notes = route['notes']
    trills = route['trill']
    t = np.linspace(0, t_total, int(round(t_total*Fs, 0)))
    f = get_new_route(t_total, Fs)
    tr_x = []
    tr_y = []
    for tr in trills:
        # [x, note, freq, duration]
        ti = tr[0]
        dist = tr[1]
        freq = tr[2]
        duration = tr[3]
        #print(tr)
        for i in range(int(freq*duration)):
            f = f + np.heaviside(t - ti - 2*i/(2*freq), 1) * dist - np.heaviside(t - ti - (2*i+1)/(2*freq), 1) * dist

    x_points = []
    y_points = []
    if len(notes):
        alt_i = dict_notes_rev[notes[0][1]]
        f += alt_i
    for n in notes:
        x_points.append(n[0])
        y_points.append(dict_notes_rev[n[1]])
        #print(type(np.heaviside(t - n[0], 1)), type(dict_notes_rev[n[1]] - alt_i))
        f += np.heaviside(t - n[0], 1) * (dict_notes_rev[n[1]] - alt_i)
        alt_i = dict_notes_rev[n[1]]
    
    for tr in trills:
        tr_x.append(tr[0])
        tr_y.append(f[int(tr[0]*len(f)/t_total)]-0.1)

    return t, f, x_points, y_points, tr_x, tr_y

