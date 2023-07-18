
 /**
 * PS Move API - An interface for the PS Move Motion Controller
 * Copyright (c) 2012, 2022 Thomas Perl <m@thp.io>
 * Copyright (c) 2012 Benjamin Venditt <benjamin.venditti@gmail.com>
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

#include "opencv2/core/core_c.h"
#include "opencv2/highgui/highgui_c.h"

#include "psmove.h"
#include "psmove_tracker.h"
#include "psmove_tracker_opencv.h"


void
usage(const char *progname)
{
    printf("Usage: %s [-exposure low|medium|high] [-h|--help]\n", progname);
}


int
main(int argc, char *argv[])
{
    PSMoveTrackerSettings settings;
    psmove_tracker_settings_set_default(&settings);
    settings.camera_mirror = true;

    char *progname = argv[0];
    ++argv;
    --argc;

    while (argc > 0) {
        if (strcmp(argv[0], "-exposure") == 0 && argc > 1) {
            ++argv;
            --argc;

            if (strcmp(argv[0], "low") == 0) {
                settings.camera_exposure = 0.1f;
            } else if (strcmp(argv[0], "medium") == 0) {
                settings.camera_exposure = 0.5f;
            } else if (strcmp(argv[0], "high") == 0) {
                settings.camera_exposure = 1.f;
            } else {
                usage(progname);
                return 1;
            }
        } else if (strcmp(argv[0], "-h") == 0 || strcmp(argv[0], "--help") == 0) {
            usage(progname);
            return 0;
        } else {
            usage(progname);
            printf("Unhandled command-line argument: %s\n", argv[0]);
            return 1;
        }

        ++argv;
        --argc;
    }

    PSMoveTracker *tracker = psmove_tracker_new_with_settings(&settings);

    if (!tracker) {
        fprintf(stderr, "Could not init PSMoveTracker.\n");
        return 1;
    }

    while ((cvWaitKey(1) & 0xFF) != 27) {
        psmove_tracker_update_image(tracker);
        psmove_tracker_update(tracker, NULL);

        IplImage *frame = psmove_tracker_opencv_get_frame(tracker);
        if (frame) {
            for (int col=0; col<7; ++col) {
                int x = col * (frame->width - 1) / 6;
                cv::line(cv::cvarrToMat(frame), cv::Point(x, 0), cv::Point(x, frame->height - 1), cvScalar(255, (col==3)?255:0, 0, 0));

                int y = col * (frame->height - 1) / 6;
                cv::line(cv::cvarrToMat(frame), cv::Point(0, y), cv::Point(frame->width - 1, y), cvScalar(0, (col==3)?255:0, 255, 0));
            }

            const auto camera_info = psmove_tracker_get_camera_info(tracker);

            CvFont fontSmall = cvFont(0.8, 1);
            CvPoint txt = cvPoint(30, 30);
            std::string tmp = format("%s %dx%d (%s)", camera_info->camera_name, camera_info->width, camera_info->height, camera_info->camera_api);
            cvPutText(frame, tmp.c_str(), txt, &fontSmall, CvScalar{255.0, 255.0, 255.0, 255.0});

            cvShowImage("live camera feed", frame);
        }
    }

    psmove_tracker_free(tracker);

    return 0;
}
