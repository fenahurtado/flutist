
 /**
 * PS Move API - An interface for the PS Move Motion Controller
 * Copyright (c) 2011 Thomas Perl <m@thp.io>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *    1. Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 **/



#include <stdio.h>
#include <stdlib.h>

#include "psmove.h"
#include "psmove_tracker.h"

int main(int argc, char* argv[])
{
    PSMove *move;
    enum PSMove_Connection_Type ctype;
    int i;

    if (!psmove_init(PSMOVE_CURRENT_VERSION)) {
        fprintf(stderr, "PS Move API init failed (wrong version?)\n");
        fflush(stdout);
        exit(1);
    }

    i = psmove_count_connected();
    printf("Connected controllers: %d\n", i);
    fflush(stdout);

    move = psmove_connect();

    if (move == NULL) {
        printf("Could not connect to default Move controller.\n"
               "Please connect one via USB or Bluetooth.\n");
        fflush(stdout);
        exit(1);
    }

    char *serial = psmove_get_serial(move);
    printf("Serial: %s\n", serial);
    fflush(stdout);
    psmove_free_mem(serial);

    ctype = psmove_connection_type(move);
    switch (ctype) {
        case Conn_USB:
            printf("Connected via USB.\n");
            fflush(stdout);
            break;
        case Conn_Bluetooth:
            printf("Connected via Bluetooth.\n");
            fflush(stdout);
            break;
        case Conn_Unknown:
            printf("Unknown connection type.\n");
            fflush(stdout);
            break;
    }

    for (i=0; i<10; i++) {
        psmove_set_leds(move, 0, 255*(i%3==0), 0);
        psmove_set_rumble(move, 255*(i%2));
        psmove_update_leds(move);
        psmove_util_sleep_ms(10*(i%10));
    }

    for (i=250; i>=0; i-=5) {
		psmove_set_leds(move, (unsigned char)i, (unsigned char)i, 0);
        psmove_set_rumble(move, 0);
        psmove_update_leds(move);
    }

    /* Enable rate limiting for LED updates */
    psmove_set_rate_limiting(move, 1);

    psmove_set_leds(move, 0, 0, 0);
    psmove_set_rumble(move, 0);
    psmove_update_leds(move);

    while (ctype != Conn_USB && !(psmove_get_buttons(move) & Btn_PS)) {
        int res = psmove_poll(move);
        if (res) {
            if (psmove_get_buttons(move) & Btn_MOVE) {
                psmove_set_rumble(move, psmove_get_trigger(move));
            }

            psmove_set_leds(move, 0, 0, psmove_get_trigger(move));

            int x1, y1, z1, x2, y2, z2, x3, y3, z3;
            psmove_get_accelerometer(move, &x1, &y1, &z1);
            psmove_get_gyroscope(move, &x2, &y2, &z2);
            psmove_get_magnetometer(move, &x3, &y3, &z3);
            printf("state %5d %5d %5d %5d %5d %5d %5d %5d %5d %5d %x\n", psmove_get_trigger(move), x1, y1, z1, x2, y2, z2, x3, y3, z3, psmove_get_buttons(move));
            fflush(stdout);
            

            // int battery = psmove_get_battery(move);

            // if (battery == Batt_CHARGING) {
            //     printf("battery charging\n");
            // } else if (battery == Batt_CHARGING_DONE) {
            //     printf("battery fully charged (on charger)\n");
            // } else if (battery >= Batt_MIN && battery <= Batt_MAX) {
            //     printf("battery level: %d / %d\n", battery, Batt_MAX);
            // } else {
            //     printf("battery level: unknown (%x)\n", battery);
            // }

            // printf("raw temperature: %d\n", psmove_get_temperature(move));
            // printf("celsius temperature: %f\n", psmove_get_temperature_in_celsius(move));

            psmove_update_leds(move);
        }
    }

    psmove_disconnect(move);

    printf("estado_final \n");
    fflush(stdout);
    return 0;
}

