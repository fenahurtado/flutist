/**
 * PS Move API - An interface for the PS Move Motion Controller
 * Copyright (c) 2012 Thomas Perl <m@thp.io>
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

#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <math.h>
#include <sys/stat.h>

#include <vector>

#include "opencv2/core/core_c.h"
#include "opencv2/imgproc/imgproc_c.h"
#include "opencv2/highgui/highgui_c.h"

#include "psmove_tracker.h"
#include "psmove_tracker_opencv.h"
#include "psmove_tracker_hue_calibration.h"

#include "../psmove_private.h"
#include "../psmove_port.h"
#include "../psmove_format.h"

#include "camera_control.h"
#include "tracker_helpers.h"

#define ROIS 4                          // the number of levels of regions of interest (roi)


/**
 * Syntactic sugar - iterate over all valid controllers of a tracker
 *
 * Usage example:
 *
 *    TrackedController *tc;
 *    for_each_controller (tracker, tc) {
 *        // do something with "tc" here
 *    }
 *
 **/
#define for_each_controller(tracker, var) \
    for (var=tracker->controllers; var<tracker->controllers+PSMOVE_TRACKER_MAX_CONTROLLERS; var++) \
        if (var->move)

struct _TrackedController {
    /* Move controller, or NULL if free slot */
    PSMove* move;

    /* Assigned RGB color of the controller */
    struct PSMove_RGBValue color;
    CvScalar assignedHSV; // Assigned color in HSV colorspace

    CvScalar eFColorHSV;		// first estimated color (HSV)
    CvScalar eColorHSV;			// estimated color (HSV)

    int roi_x, roi_y;			// x/y - Coordinates of the ROI
    int roi_level; 	 			// the current index for the level of ROI
    float mx, my;				// x/y - Coordinates of center of mass of the blob
    float x, y, r;				// x/y - Coordinates of the controllers sphere and its radius
    int search_tile; 			// current search quadrant when controller is not found (reset to 0 if found)
    float rs;					// a smoothed variant of the radius

    float q1, q2, q3; // Calculated quality criteria from the tracker

    int is_tracked;				// 1 if tracked 0 otherwise
    long last_color_update;	// the timestamp when the last color adaption has been performed
    bool auto_update_leds;
};

typedef struct _TrackedController TrackedController;


/**
 * Parameters of the Pearson type VII distribution
 * Source: http://fityk.nieto.pl/model.html
 * Used for calculating the distance from the radius
 **/
struct PSMoveTracker_DistanceParameters {
    float height;
    float center;
    float hwhm;
    float shape;
};

struct _PSMoveTracker {
    _PSMoveTracker(CameraControl *cc, const PSMoveTrackerSettings *init_settings)
        : cc(cc)
        , cc_settings(camera_control_backup_system_settings(cc))
        , settings(*init_settings)
        , rHSV(cvScalar(settings.color_hue_filter_range,
                        settings.color_saturation_filter_range,
                        settings.color_value_filter_range,
                        0))
        , storage(cvCreateMemStorage(0))
        , camera_info(camera_control_get_camera_info(cc))
    {
        camera_control_read_calibration(cc, settings.camera_calibration_filename);

        // update mirror and exposure state
        psmove_tracker_set_mirror(this, settings.camera_mirror);
        psmove_tracker_set_exposure(this, settings.camera_exposure);

        // We need to grab an image from the camera to determine the frame size
        while (!frame) {
            psmove_tracker_update_image(this);
        }

        // prepare ROI data structures

        /* Define the size of the biggest ROI */
        int size = MIN(frame->width, frame->height) / 2;

        settings.search_tile_width = size;
        settings.search_tile_height = size;

        settings.search_tiles_horizontal = (frame->width + settings.search_tile_width - 1) / settings.search_tile_width;
        int search_tiles_vertical = (frame->height + settings.search_tile_height - 1) / settings.search_tile_height;
        settings.search_tiles_count = settings.search_tiles_horizontal * search_tiles_vertical;

        if (settings.search_tiles_count % 2 == 0) {
            /**
             * search_tiles_count must be uneven, so that when picking every second
             * tile, we still "visit" every tile after two scans when we wrap:
             *
             *  ABA
             *  BAB
             *  ABA -> OK, first run = A, second run = B
             *
             *  ABAB
             *  ABAB -> NOT OK, first run = A, second run = A
             *
             * Incrementing the count will make the algorithm visit the lower right
             * item twice, but will then cause the second run to visit 'B's.
             *
             * We pick every second tile, so that we only need half the time to
             * sweep through the whole image (which usually means faster recovery).
             **/
            settings.search_tiles_count++;
        }

        for (int i = 0; i < ROIS; i++) {
            roiI[i] = cvCreateImage(cvSize(size, size), frame->depth, 3);
            roiM[i] = cvCreateImage(cvSize(size, size), frame->depth, 1);

            /* Smaller rois are 70% of the previous level */
            size *= 0.7f;
        }

        // prepare structure used for erode and dilate in calibration process
        int ks = 5; // Kernel Size
        int kc = 2; // Kernel Center
        kCalib = cvCreateStructuringElementEx(ks, ks, kc, kc, CV_SHAPE_RECT, NULL);
    }

    _PSMoveTracker(const PSMoveTracker &) = delete;
    _PSMoveTracker(PSMoveTracker &&) = delete;
    _PSMoveTracker &operator=(const PSMoveTracker &) = delete;
    _PSMoveTracker &operator=(PSMoveTracker &&) = delete;

    ~_PSMoveTracker()
    {
        if (frame_rgb) {
            cvReleaseImage(&frame_rgb);
        }

        camera_control_restore_system_settings(cc, cc_settings);

        for (int i=0; i < ROIS; i++) {
            cvReleaseImage(&roiM[i]);
            cvReleaseImage(&roiI[i]);
        }
        cvReleaseStructuringElement(&kCalib);

        camera_control_delete(cc);

        cvReleaseMemStorage(&storage);
    }

    CameraControl *cc { nullptr };
    struct CameraControlSystemSettings *cc_settings { nullptr };

    PSMoveTrackerSettings settings;  // Camera and tracker algorithm settings. Generally do not change after startup & calibration.

    IplImage *frame { nullptr }; // the current frame of the camera
    IplImage *frame_rgb { nullptr }; // the frame as tightly packed RGB data
    IplImage *roiI[ROIS] {}; // array of images for each level of roi (colored)
    IplImage *roiM[ROIS] {}; // array of images for each level of roi (greyscale)
    IplConvKernel *kCalib { nullptr }; // kernel used for morphological operations during calibration
    CvScalar rHSV; // the range of the color filter

    /**
     * Experimentally-determined parameters for a PS3 Eye camera
     * in wide angle mode with a PS Move, color = (255, 0, 255)
     **/
    struct PSMoveTracker_DistanceParameters distance_parameters {
        /* height = */ 517.281f,
        /* center = */ 1.297338f,
        /* hwhm = */ 3.752844f,
        /* shape = */ 0.4762335f,
    };

    TrackedController controllers[PSMOVE_TRACKER_MAX_CONTROLLERS] {}; // controller data

    CvMemStorage *storage { nullptr }; // use to store the result of cvFindContour and cvHughCircles
    long duration; // duration of tracking operation, in ms

    // internal variables (debug)
    float debug_fps { 0.f }; // the current FPS achieved by "psmove_tracker_update"

    // Stored results of hue calibration
    std::vector<psmove::tracker::HueCalibrationInfo> hue_calibration_info;

    // Color mapping for blinking calibration
    std::vector<psmove::tracker::HueCalibrationInfo> color_mapping_info;

    PSMoveCameraInfo camera_info;
};

// -------- START: internal functions only

/**
 * Find the TrackedController * for a given PSMove * instance
 *
 * if move == NULL, the next free slot will be returned
 *
 * Returns the TrackedController * instance, or NULL if not found
 **/
TrackedController *
psmove_tracker_find_controller(PSMoveTracker *tracker, PSMove *move);

/**
 * Wait for a given time for a frame from the tracker
 *
 * tracker - A valid PSMoveTracker * instance
 * frame - A pointer to an IplImage * to store the frame
 * delay_ms - The delay to wait for the frame, in milliseconds
 **/
void
psmove_tracker_wait_for_frame(PSMoveTracker *tracker, IplImage **frame, int delay_ms);

/**
 * This function switches the sphere of the given PSMove on to the given color and takes
 * a picture via the given capture. Then it switches it of and takes a picture again. A difference image
 * is calculated from these two images. It stores the image of the lit sphere and
 * of the diff-image in the passed parameter "on" and "diff". Before taking
 * a picture it waits for the specified delay (in microseconds).
 *
 * tracker - the tracker that contains the camera control
 * move    - the PSMove controller to use
 * rgb     - the RGB color to use to lit the sphere
 * on	   - the pre-allocated image to store the captured image when the sphere is lit
 * diff    - the pre-allocated image to store the calculated diff-image
 * delay_ms- the time to wait before taking a picture (in milliseconds)
 **/
void
psmove_tracker_get_diff(PSMoveTracker* tracker, PSMove* move,
        struct PSMove_RGBValue rgb, IplImage* on, IplImage* diff, int delay_ms,
        float dimming_factor);

/**
 * This function seths the rectangle of the ROI and assures that the itis always within the bounds
 * of the camera image.
 *
 * tracker          - A valid PSMoveTracker * instance
 * tc         - The TrackableController containing the roi to check & fix
 * roi_x	  - the x-part of the coordinate of the roi
 * roi_y	  - the y-part of the coordinate of the roi
 * roi_width  - the width of the roi
 * roi_height - the height of the roi
 * cam_width  - the width of the camera image
 * cam_height - the height of the camera image
 **/
void psmove_tracker_set_roi(PSMoveTracker* tracker, TrackedController* tc, int roi_x, int roi_y, int roi_width, int roi_height);

/**
 * This function is just the internal implementation of "psmove_tracker_update"
 */
int psmove_tracker_update_controller(PSMoveTracker* tracker, TrackedController *tc);

/*
 *  This finds the biggest contour within the given image.
 *
 *  img  		- (in) 	the binary image to search for contours
 *  stor 		- (out) a storage that can be used to save the result of this function
 *  resContour 	- (out) points to the biggest contour found within the image
 *  resSize 	- (out)	the size of that contour in px�
 */
void psmove_tracker_biggest_contour(IplImage* img, CvMemStorage* stor, CvSeq** resContour, float* resSize);

/*
 * This returns a subjective distance between the first estimated (during calibration process) color and the currently estimated color.
 * Subjective, because it takes the different color components not equally into account.
 *    Result calculates like: abs(c1.h-c2.h) + abs(c1.s-c2.s)*0.5 + abs(c1.v-c2.v)*0.5
 *
 * tc - The controller whose first/current color estimation distance should be calculated.
 *
 * Returns: a subjective distance
 */
float psmove_tracker_hsvcolor_diff(TrackedController* tc);

/*
 * This will estimate the position and the radius of the orb.
 * It will calcualte the radius by findin the two most distant points
 * in the contour. And its by choosing the mid point of those two.
 *
 * cont 	- (in) 	The contour representing the orb.
 * x            - (out) The X coordinate of the center.
 * y            - (out) The Y coordinate of the center.
 * radius	- (out) The radius of the contour that is calculated here.
 */
void
psmove_tracker_estimate_circle_from_contour(CvSeq* cont, float *x, float *y, float* radius);

/*
 * This function return a optimal ROI center point for a given Tracked controller.
 * On very fast movements, it may happen that the orb is visible in the ROI, but resides
 * at its border. This function will simply look for the biggest blob in the ROI and return a
 * point so that that blob would be in the center of the ROI.
 *
 * tc - (in) The controller whose ROI centerpoint should be adjusted.
 * tracker  - (in) The PSMoveTracker to use.
 * center - (out) The better center point for the current ROI
 *
 * Returns: nonzero if a new point was found, zero otherwise
 */
int
psmove_tracker_center_roi_on_controller(TrackedController* tc, PSMoveTracker* tracker, CvPoint *center);

static bool
psmove_tracker_color_is_used(PSMoveTracker *tracker, struct PSMove_RGBValue color);

enum PSMoveTracker_Status
psmove_tracker_enable_with_color_internal(PSMoveTracker *tracker, PSMove *move, struct PSMove_RGBValue color);

/*
 * This function reads old calibration color values and tries to track the controller with that color.
 * if it works, the function returns 1, 0 otherwise.
 * Can help to speed up calibration process on application startup.
 *
 * tracker     - (in) A valid PSMoveTracker
 * move  - (in) A valid PSMove controller
 * rgb - (in) The color the PSMove controller's sphere will be lit.
 */

static bool
psmove_tracker_old_color_is_tracked(PSMoveTracker *tracker, PSMove *move, struct PSMove_RGBValue rgb);

/**
 * Lookup a camera-visible color value
 **/
static bool
psmove_tracker_lookup_color(PSMoveTracker *tracker, struct PSMove_RGBValue rgb, CvScalar *colorHSV, float *dimming);

/**
 * Remember a color value after calibration
 **/
void
psmove_tracker_remember_color(PSMoveTracker *tracker, struct PSMove_RGBValue rgb, CvScalar colorHSV, float dimming);

// -------- END: internal functions only

void
psmove_tracker_settings_set_default(PSMoveTrackerSettings *settings)
{
    settings->camera_frame_width = -1;
    settings->camera_frame_height = -1;
    settings->camera_frame_rate = -1;
    settings->camera_exposure = 0.3f;
    settings->camera_mirror = false;
    settings->calibration_blink_delay_ms = 50;
    settings->calibration_diff_t = 20;
    settings->calibration_min_size = 50;
    settings->calibration_max_distance = 30;
    settings->calibration_size_std = 10;
    settings->color_hue_filter_range = 8;
    settings->color_saturation_filter_range = 85;
    settings->color_value_filter_range = 85;
    settings->tracker_adaptive_xy = 1;
    settings->tracker_adaptive_z = 1;
    settings->color_adaption_quality_t = 35.f;
    settings->color_update_rate = 1.f;
    settings->search_tile_width = 0;
    settings->search_tile_height = 0;
    settings->search_tiles_horizontal = 0;
    settings->search_tiles_count = 0;
    settings->roi_adjust_fps_t = 160;
    settings->tracker_quality_t1 = 0.3f;
    settings->tracker_quality_t2 = 0.7f;
    settings->tracker_quality_t3 = 4.7f;
    settings->color_update_quality_t1 = 0.8f;
    settings->color_update_quality_t2 = 0.2f;
    settings->color_update_quality_t3 = 6.f;
    settings->camera_calibration_filename = nullptr;
}

void
psmove_tracker_set_auto_update_leds(PSMoveTracker *tracker, PSMove *move,
        bool auto_update_leds)
{
    psmove_return_if_fail(tracker != NULL);
    psmove_return_if_fail(move != NULL);
    TrackedController *tc = psmove_tracker_find_controller(tracker, move);
    psmove_return_if_fail(tc != NULL);
    tc->auto_update_leds = auto_update_leds;
}


bool
psmove_tracker_get_auto_update_leds(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_val_if_fail(tracker != NULL, false);
    psmove_return_val_if_fail(move != NULL, false);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);
    psmove_return_val_if_fail(tc != NULL, false);
    return tc->auto_update_leds;
}

void
psmove_tracker_enable_deinterlace(PSMoveTracker *tracker,
        bool enabled)
{
    psmove_return_if_fail(tracker != NULL);
    psmove_return_if_fail(tracker->cc != NULL);

    camera_control_set_deinterlace(tracker->cc, enabled);
}

void
psmove_tracker_set_mirror(PSMoveTracker *tracker,
        bool enabled)
{
    psmove_return_if_fail(tracker != NULL);

    tracker->settings.camera_mirror = enabled;
    camera_control_set_parameters(tracker->cc, tracker->settings.camera_exposure, tracker->settings.camera_mirror);
}

bool
psmove_tracker_get_mirror(PSMoveTracker *tracker)
{
    psmove_return_val_if_fail(tracker != NULL, false);

    return tracker->settings.camera_mirror;
}

PSMoveTracker *
psmove_tracker_new()
{
    PSMoveTrackerSettings settings;
    psmove_tracker_settings_set_default(&settings);
    return psmove_tracker_new_with_settings(&settings);
}

PSMoveTracker *
psmove_tracker_new_with_settings(PSMoveTrackerSettings *settings)
{
    return psmove_tracker_new_with_camera_and_settings(-1, settings);
}

PSMoveTracker *
psmove_tracker_new_with_camera(int camera)
{
    PSMoveTrackerSettings settings;
    psmove_tracker_settings_set_default(&settings);
    return psmove_tracker_new_with_camera_and_settings(camera, &settings);
}

PSMoveTracker *
psmove_tracker_new_with_camera_and_settings(int camera, PSMoveTrackerSettings *settings)
{
    CameraControl *cc = camera_control_new_with_settings(camera,
            settings->camera_frame_width, settings->camera_frame_height, settings->camera_frame_rate);

    if (!cc) {
        return nullptr;
    }

    return new PSMoveTracker(cc, settings);
}

int
psmove_tracker_count_connected()
{
	return camera_control_count_connected();
}

bool
psmove_tracker_get_next_unused_color(PSMoveTracker *tracker,
         unsigned char *r, unsigned char *g, unsigned char *b)
{
    /* Preset colors - use them in ascending order if not used yet */
    static constexpr const PSMove_RGBValue PRESET_COLORS[] = {
        {0xFF, 0x00, 0xFF}, /* magenta */
        {0x00, 0xFF, 0xFF}, /* cyan */
        {0xFF, 0xFF, 0x00}, /* yellow */
        {0xFF, 0x00, 0x00}, /* red */
        {0x00, 0x00, 0xFF}, /* blue */
        {0x00, 0xFF, 0x00}, /* green */
    };

    for (auto &color: PRESET_COLORS) {
        if (!psmove_tracker_color_is_used(tracker, color)) {
            if (r) *r = color.r;
            if (g) *g = color.g;
            if (b) *b = color.b;

            return true;
        }
    }

    return false;
}

void
psmove_tracker_set_exposure(PSMoveTracker *tracker, float exposure)
{
    tracker->settings.camera_exposure = exposure;
    camera_control_set_parameters(tracker->cc, tracker->settings.camera_exposure, tracker->settings.camera_mirror);
}

float
psmove_tracker_get_exposure(PSMoveTracker *tracker)
{
    return tracker->settings.camera_exposure;
}

void
psmove_tracker_reset_color_calibration(PSMoveTracker *tracker)
{
    tracker->hue_calibration_info.clear();
    tracker->color_mapping_info.clear();
}

static const psmove::tracker::HueCalibrationInfo *
psmove_tracker_get_next_unused_hue(PSMoveTracker *tracker)
{
    for (auto &info: tracker->hue_calibration_info) {
        bool found = false;

        TrackedController *tc;
        for_each_controller(tracker, tc) {
            if (tc->move != NULL) {
                if (int(info.hue) == int(tc->assignedHSV.val[0])) {
                    found = true;
                }
            }
        }

        if (!found) {
            return &info;
        }
    }

    return nullptr;
}

static enum PSMoveTracker_Status
psmove_tracker_enable_with_hue_internal(PSMoveTracker *tracker, PSMove *move, const psmove::tracker::HueCalibrationInfo *info)
{
    // Find the next free slot to use as TrackedController
    TrackedController *tc = psmove_tracker_find_controller(tracker, NULL);

    if (tc != NULL) {
        tc->move = move;

        CvScalar rgb = info->rgb();

        tc->color.r = rgb.val[0] * info->dimming;
        tc->color.g = rgb.val[1] * info->dimming;
        tc->color.b = rgb.val[2] * info->dimming;
        tc->auto_update_leds = true;

        tc->eColorHSV = tc->eFColorHSV = cvScalar(info->cam_hsv[0], info->cam_hsv[1], info->cam_hsv[2]);
        tc->assignedHSV = cvScalar(info->hue, 255.0, 255.0);

        return Tracker_CALIBRATED;
    }

    return Tracker_CALIBRATION_ERROR;
}

enum PSMoveTracker_Status
psmove_tracker_enable(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_val_if_fail(tracker != NULL, Tracker_CALIBRATION_ERROR);
    psmove_return_val_if_fail(move != NULL, Tracker_CALIBRATION_ERROR);

    // Switch off the controller and all others while enabling another one
    TrackedController *tc;
    for_each_controller(tracker, tc) {
        psmove_set_leds(tc->move, 0, 0, 0);
        psmove_update_leds(tc->move);
    }
    psmove_set_leds(move, 0, 0, 0);
    psmove_update_leds(move);

    auto info = psmove_tracker_get_next_unused_hue(tracker);
    if (info != nullptr) {
        return psmove_tracker_enable_with_hue_internal(tracker, move, info);
    }

    struct PSMove_RGBValue color;
    if (psmove_tracker_get_next_unused_color(tracker, &color.r, &color.g, &color.b)) {
        return psmove_tracker_enable_with_color_internal(tracker, move, color);
    }

    /* No colors are available anymore */
    return Tracker_CALIBRATION_ERROR;
}

bool
psmove_tracker_old_color_is_tracked(PSMoveTracker *tracker, PSMove *move, struct PSMove_RGBValue rgb)
{
    CvScalar colorHSV;
    float dimming = 1.f;

    if (!psmove_tracker_lookup_color(tracker, rgb, &colorHSV, &dimming)) {
        return false;
    }

    TrackedController *tc = psmove_tracker_find_controller(tracker, NULL);

    if (!tc) {
        return false;
    }

    tc->move = move;
    tc->color = rgb;
    tc->color.r *= dimming;
    tc->color.g *= dimming;
    tc->color.b *= dimming;
    tc->auto_update_leds = true;

    tc->eColorHSV = tc->eFColorHSV = colorHSV;
    tc->assignedHSV = th_rgb2hsv(cvScalar(rgb.r, rgb.g, rgb.b, 255.0));

    /* Try to track the controller, give up after 10 iterations */
    for (int i=0; i<10; i++) {
        psmove_set_leds(move, rgb.r * dimming, rgb.g * dimming, rgb.b * dimming);
        psmove_update_leds(move);
        psmove_port_sleep_ms(10); // wait 10ms - ok, since we're not blinking
        psmove_tracker_update_image(tracker);
        psmove_tracker_update(tracker, move);

        if (tc->is_tracked) {
            // TODO: Verify quality criteria to avoid bogus tracking
            return true;
        }
    }

    psmove_tracker_disable(tracker, move);
    return false;
}

bool
psmove_tracker_lookup_color(PSMoveTracker *tracker, struct PSMove_RGBValue rgb, CvScalar *colorHSV, float *dimming)
{
    CvScalar hsv = th_rgb2hsv(cvScalar(rgb.r, rgb.g, rgb.b));

    for (const auto &info: tracker->color_mapping_info) {
        if (int(info.hue) == int(hsv.val[0])) {
            *colorHSV = cvScalar(info.cam_hsv[0], info.cam_hsv[1], info.cam_hsv[2]);
            *dimming = info.dimming;

            return true;
        }
    }

    return false;
}

void
psmove_tracker_remember_color(PSMoveTracker *tracker, struct PSMove_RGBValue rgb, CvScalar colorHSV, float dimming)
{
    CvScalar hsv = th_rgb2hsv(cvScalar(rgb.r, rgb.g, rgb.b));

    for (auto &info: tracker->color_mapping_info) {
        if (int(info.hue) == int(hsv.val[0])) {
            info = psmove::tracker::HueCalibrationInfo(hsv.val[0], dimming, colorHSV);
            return;
        }
    }

    tracker->color_mapping_info.emplace_back(hsv.val[0], dimming, colorHSV);
}

enum PSMoveTracker_Status
psmove_tracker_enable_with_color(PSMoveTracker *tracker, PSMove *move,
        unsigned char r, unsigned char g, unsigned char b)
{
    psmove_return_val_if_fail(tracker != NULL, Tracker_CALIBRATION_ERROR);
    psmove_return_val_if_fail(move != NULL, Tracker_CALIBRATION_ERROR);

    struct PSMove_RGBValue rgb = { r, g, b };
    return psmove_tracker_enable_with_color_internal(tracker, move, rgb);
}

static bool
psmove_tracker_blinking_calibration(PSMoveTracker *tracker, PSMove *move,
        struct PSMove_RGBValue rgb, CvScalar &colorHSV, float &dimming)
{
    psmove_tracker_update_image(tracker);
    IplImage* frame = tracker->frame;
    assert(frame != NULL);

    // Switch off all other controllers for better measurements
    TrackedController *tc;
    for_each_controller(tracker, tc) {
        psmove_set_leds(tc->move, 0, 0, 0);
        psmove_update_leds(tc->move);
    }

    // number of diff images to create during calibration
    static constexpr const size_t BLINKS = 2;

    IplImage *mask = NULL;
    IplImage *images[BLINKS]; // array of images saved during calibration for estimation of sphere color
    IplImage *diffs[BLINKS]; // array of masks saved during calibration for estimation of sphere color

    for (size_t i = 0; i < BLINKS; i++) {
        // allocate the images
        images[i] = cvCreateImage(cvGetSize(frame), frame->depth, 3);
        diffs[i] = cvCreateImage(cvGetSize(frame), frame->depth, 1);
    }
    double sizes[BLINKS]; // array of blob sizes saved during calibration for estimation of sphere color
    float sizeBest = 0;
    CvSeq *contourBest = NULL;

    CvScalar origHSV = th_rgb2hsv(cvScalar(rgb.r, rgb.g, rgb.b, 255.0));

    psmove::tracker::ColorCalibrationCollection color_calibration_collection;

    for (float try_dimming=1.f; try_dimming > 0.1f; try_dimming *= 0.4f) {
        for (size_t i = 0; i < BLINKS; i++) {
            // create a diff image
            psmove_tracker_get_diff(tracker, move, rgb, images[i], diffs[i], tracker->settings.calibration_blink_delay_ms, try_dimming);
        }

        // put the diff images together to get hopefully only one intersection region
        // the region at which the controllers sphere resides.
        mask = diffs[0];
        for (size_t i=1; i<BLINKS; i++) {
            cvAnd(mask, diffs[i], mask, NULL);
        }

        // find the biggest contour and repaint the blob where the sphere is expected
        psmove_tracker_biggest_contour(diffs[0], tracker->storage, &contourBest, &sizeBest);
        cvSet(mask, TH_COLOR_BLACK, NULL);
        if (contourBest) {
            cvDrawContours(mask, contourBest, TH_COLOR_WHITE, TH_COLOR_WHITE, -1, CV_FILLED, 8, cvPoint(0, 0));
        }
        cvClearMemStorage(tracker->storage);

        // calculate the average color from the first image (images[0] is in BGR colorspace)
        CvScalar cam_hsv = th_rgb2hsv(th_bgr2rgb(cvAvg(images[0], mask)));

        auto info = psmove::tracker::HueCalibrationInfo(origHSV.val[0], try_dimming, cam_hsv);
        color_calibration_collection.add(info);

        PSMOVE_INFO("Dimming: %.2f, H: %.2f, S: %.2f, V: %.2f --> score: %f", try_dimming,
                cam_hsv.val[0], cam_hsv.val[1], cam_hsv.val[2],
                info.penalty_score());
    }

    auto candidates = color_calibration_collection.build();

    psmove::tracker::HueCalibrationInfo best;

    if (!candidates.empty()) {
        best = candidates.front();
    }

    dimming = best.dimming;
    colorHSV = cvScalar(best.cam_hsv[0], best.cam_hsv[1], best.cam_hsv[2], 255.0);

    // Create new diff images based on the best dimming value
    // TODO: If we save the images and diffs above, we could re-use them here
    for (size_t i = 0; i < BLINKS; i++) {
        psmove_tracker_get_diff(tracker, move, rgb, images[i], diffs[i], tracker->settings.calibration_blink_delay_ms, dimming);
    }

    size_t valid_countours = 0;

    // calculate upper & lower bounds for the color filter
    CvScalar min = th_scalar_sub(colorHSV, tracker->rHSV);
    CvScalar max = th_scalar_add(colorHSV, tracker->rHSV);

    CvPoint firstPosition;
    for (size_t i=0; i<BLINKS; i++) {
        // Convert to HSV, then apply the color range filter to the mask
        cvCvtColor(images[i], images[i], CV_BGR2HSV);
        cvInRangeS(images[i], min, max, mask);

        // use morphological operations to further remove noise
        cvErode(mask, mask, tracker->kCalib, 1);
        cvDilate(mask, mask, tracker->kCalib, 1);

        // find the biggest contour in the image and save its location and size
        psmove_tracker_biggest_contour(mask, tracker->storage, &contourBest, &sizeBest);
        sizes[i] = 0;
        float dist = FLT_MAX;
        CvRect bBox;
        if (contourBest) {
            bBox = cvBoundingRect(contourBest, 0);
            if (i == 0) {
                firstPosition = cvPoint(bBox.x, bBox.y);
            }
            dist = (float)sqrt(pow(firstPosition.x - bBox.x, 2) + pow(firstPosition.y - bBox.y, 2));
            sizes[i] = sizeBest;
        }

        // CHECK for errors (no contour, more than one contour, or contour too small)
        if (!contourBest) {
            // No contour
        } else if (sizes[i] <= tracker->settings.calibration_min_size) {
            // Too small
        } else if (dist >= tracker->settings.calibration_max_distance) {
            // Too far apart
        } else {
            // all checks passed, increase the number of valid contours
            valid_countours++;
        }
        cvClearMemStorage(tracker->storage);

    }

    // clean up all temporary images
    for (size_t i=0; i<BLINKS; i++) {
        cvReleaseImage(&images[i]);
        cvReleaseImage(&diffs[i]);
    }

    // CHECK if sphere was found in each BLINK image
    if (valid_countours < BLINKS) {
        return false;
    }

    // CHECK if the size of the found contours are similar
    double sizeVariance, sizeAverage;
    th_stats(sizes, BLINKS, &sizeVariance, &sizeAverage);
    if (sqrt(sizeVariance) >= (sizeAverage / 100.0 * tracker->settings.calibration_size_std)) {
        return false;
    }

    return !candidates.empty();
}


enum PSMoveTracker_Status
psmove_tracker_enable_with_color_internal(PSMoveTracker *tracker, PSMove *move,
        struct PSMove_RGBValue rgb)
{
    // check if the controller is already enabled!
    if (psmove_tracker_find_controller(tracker, move)) {
        return Tracker_CALIBRATED;
    }

    // cannot use the same color for two different controllers
    if (psmove_tracker_color_is_used(tracker, rgb)) {
        return Tracker_CALIBRATION_ERROR;
    }

    // try to track the controller with the old color, if it works we are done
    if (psmove_tracker_old_color_is_tracked(tracker, move, rgb)) {
        return Tracker_CALIBRATED;
    }

    CvScalar colorHSV;
    float dimming = 1.f;
    if (psmove_tracker_blinking_calibration(tracker, move, rgb, colorHSV, dimming)) {
        // Find the next free slot to use as TrackedController
        TrackedController *tc = psmove_tracker_find_controller(tracker, NULL);

        if (tc != NULL) {
            tc->move = move;
            tc->color = rgb;
            tc->color.r *= dimming;
            tc->color.g *= dimming;
            tc->color.b *= dimming;

            tc->auto_update_leds = true;

            psmove_tracker_remember_color(tracker, rgb, colorHSV, dimming);
            tc->eColorHSV = tc->eFColorHSV = colorHSV;
            tc->assignedHSV = th_rgb2hsv(cvScalar(rgb.r, rgb.g, rgb.b, 255.0));

            return Tracker_CALIBRATED;
        }
    }

    return Tracker_CALIBRATION_ERROR;
}

int
psmove_tracker_get_color(PSMoveTracker *tracker, PSMove *move,
        unsigned char *r, unsigned char *g, unsigned char *b)
{
    psmove_return_val_if_fail(tracker != NULL, 0);
    psmove_return_val_if_fail(move != NULL, 0);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);

    if (tc) {
        *r = tc->color.r;
        *g = tc->color.g;
        *b = tc->color.b;

        return 1;
    }

    return 0;
}

int
psmove_tracker_get_camera_color(PSMoveTracker *tracker, PSMove *move,
        unsigned char *r, unsigned char *g, unsigned char *b)
{
    psmove_return_val_if_fail(tracker != NULL, 0);
    psmove_return_val_if_fail(move != NULL, 0);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);

    if (tc) {
        CvScalar rgb = th_hsv2rgb(tc->eColorHSV);

        *r = (unsigned char)(rgb.val[0]);
        *g = (unsigned char)(rgb.val[1]);
        *b = (unsigned char)(rgb.val[2]);

        return 1;
    }

    return 0;
}

void
psmove_tracker_disable(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_if_fail(tracker != NULL);
    psmove_return_if_fail(move != NULL);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);

    if (tc) {
        // Clear the tracked controller state - also sets move = NULL
        memset(tc, 0, sizeof(TrackedController));

        // XXX: If we "defrag" tracker->controllers to avoid holes with NULL
        // controllers, we can simplify psmove_tracker_find_controller() and
        // abort search at the first encounter of a NULL controller
    }
}

enum PSMoveTracker_Status
psmove_tracker_get_status(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_val_if_fail(tracker != NULL, Tracker_CALIBRATION_ERROR);
    psmove_return_val_if_fail(move != NULL, Tracker_CALIBRATION_ERROR);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);

    if (tc) {
        if (tc->is_tracked) {
            return Tracker_TRACKING;
        } else {
            return Tracker_CALIBRATED;
        }
    }

    return Tracker_NOT_CALIBRATED;
}

IplImage *
psmove_tracker_opencv_get_frame(PSMoveTracker *tracker)
{
    return tracker->frame;
}

PSMoveTrackerRGBImage
psmove_tracker_get_image(PSMoveTracker *tracker)
{
    PSMoveTrackerRGBImage result = { NULL, 0, 0 };

    if (tracker != NULL) {
        result.width = tracker->frame->width;
        result.height = tracker->frame->height;

        if (tracker->frame_rgb == NULL) {
            tracker->frame_rgb = cvCreateImage(cvSize(result.width, result.height),
                    IPL_DEPTH_8U, 3);
        }

        cvCvtColor(tracker->frame, tracker->frame_rgb, CV_BGR2RGB);
        result.data = tracker->frame_rgb->imageData;
    }

    return result;
}

void psmove_tracker_update_image(PSMoveTracker *tracker) {
    psmove_return_if_fail(tracker != NULL);

    tracker->frame = camera_control_query_frame(tracker->cc);

#if !defined(CAMERA_CONTROL_USE_PS3EYE_DRIVER) && !defined(__linux)
    // PS3EyeDriver, CLEyeDriver, and v4l support flipping the camera image in
    // hardware (or in the driver). Manual flipping is only required if we are
    // using none of these ways to configure the camera and thus have no way
    // to enable flipping in hardware (or the driver).
    if (tracker->settings.camera_mirror) {
        // mirror image horizontally, i.e. flip left to right
        cvFlip(tracker->frame, NULL, 1);
    }
#endif
}

int
psmove_tracker_update_controller(PSMoveTracker *tracker, TrackedController *tc)
{
    float x, y;
    int i = 0;
    int sphere_found = 0;

    if (tc->auto_update_leds) {
        unsigned char r, g, b;
        psmove_tracker_get_color(tracker, tc->move, &r, &g, &b);
        psmove_set_leds(tc->move, r, g, b);
        psmove_update_leds(tc->move);
    }

    // calculate upper & lower bounds for the color filter
    CvScalar min = th_scalar_sub(tc->eColorHSV, tracker->rHSV);
    CvScalar max = th_scalar_add(tc->eColorHSV, tracker->rHSV);

	// this is the tracking algorithm
	for (;;) {
		// get pointers to data structures for the given ROI-Level
		IplImage *roi_i = tracker->roiI[tc->roi_level];
		IplImage *roi_m = tracker->roiM[tc->roi_level];

		// adjust the ROI, so that the blob is fully visible, but only if we have a reasonable FPS
        if (tracker->debug_fps > tracker->settings.roi_adjust_fps_t) {
			// TODO: check for validity differently
			CvPoint nRoiCenter;
            if (psmove_tracker_center_roi_on_controller(tc, tracker, &nRoiCenter)) {
				psmove_tracker_set_roi(tracker, tc, nRoiCenter.x, nRoiCenter.y, roi_i->width, roi_i->height);
			}
		}

		// apply the ROI
		cvSetImageROI(tracker->frame, cvRect(tc->roi_x, tc->roi_y, roi_i->width, roi_i->height));
		cvCvtColor(tracker->frame, roi_i, CV_BGR2HSV);

		// apply color filter
		cvInRangeS(roi_i, min, max, roi_m);

		// find the biggest contour in the image
		float sizeBest = 0;
		CvSeq* contourBest = NULL;
		psmove_tracker_biggest_contour(roi_m, tracker->storage, &contourBest, &sizeBest);

		if (contourBest) {
			CvMoments mu; // ImageMoments are use to calculate the center of mass of the blob
			CvRect br = cvBoundingRect(contourBest, 0);

			// restore the biggest contour
			cvSet(roi_m, TH_COLOR_BLACK, NULL);
			cvDrawContours(roi_m, contourBest, TH_COLOR_WHITE, TH_COLOR_WHITE, -1, CV_FILLED, 8, cvPoint(0, 0));
			// calucalte image-moments
			cvMoments(roi_m, &mu, 0);
			// calucalte the mass center
            CvPoint p = cvPoint((int)(mu.m10 / mu.m00), (int)(mu.m01 / mu.m00));
            CvPoint oldMCenter = cvPoint((int)tc->mx, (int)tc->my);
			tc->mx = (float)p.x + tc->roi_x;
			tc->my = (float)p.y + tc->roi_y;
			CvPoint newMCenter = cvPoint((int)tc->mx, (int)tc->my);

			// remember the old radius and calcutlate the new x/y position and radius of the found contour
			float oldRadius = tc->r;
			// estimate x/y position and radius of the sphere
			psmove_tracker_estimate_circle_from_contour(contourBest, &x, &y, &tc->r);

			// apply radius-smoothing if enabled
            if (tracker->settings.tracker_adaptive_z) {
				// calculate the difference between calculated radius and the smoothed radius of the past
				float rDiff = (float)fabs(tc->rs - tc->r);
				// calcualte a adaptive smoothing factor
				// a big distance leads to no smoothing, a small one to strong smoothing
				float rf = MIN(rDiff/4+0.15f,1);

				// apply adaptive smoothing of the radius
				tc->rs = tc->rs * (1 - rf) + tc->r * rf;
				tc->r = tc->rs;
			}

			// apply x/y coordinate smoothing if enabled
			if (tracker->settings.tracker_adaptive_xy) {
				// a big distance between the old and new center of mass results in no smoothing
				// a little one to strong smoothing
				float diff = (float)sqrt(th_dist_squared(oldMCenter, newMCenter));
				float f = MIN(diff / 7 + 0.15f, 1);
				// apply adaptive smoothing
				tc->x = tc->x * (1 - f) + (x + tc->roi_x) * f;
				tc->y = tc->y * (1 - f) + (y + tc->roi_y) * f;
			} else {
				// do NOT apply adaptive smoothing
				tc->x = x + tc->roi_x;
				tc->y = y + tc->roi_y;
			}

			// calculate the quality of the tracking
			int pixelInBlob = cvCountNonZero(roi_m);
			float pixelInResult = (float)(tc->r * tc->r * M_PI);
                        tc->q1 = 0;
                        tc->q2 = FLT_MAX;
                        tc->q3 = tc->r;

			// decrease TQ1 by half if below 20px (gives better results if controller is far away)
			if (pixelInBlob < 20) {
				tc->q1 /= 2;
                        }

			// The quality checks are all performed on the radius of the blob
			// its old radius and size.
			tc->q1 = pixelInBlob / pixelInResult;

			// always check pixel-ratio and minimal size
            sphere_found = tc->q1 > tracker->settings.tracker_quality_t1 && tc->q3 > tracker->settings.tracker_quality_t3;

			// use the mass center if the quality is very good
			// TODO: make 0.85 as a CONST
			if (tc->q1 > 0.85) {
				tc->x = tc->mx;
				tc->y = tc->my;
			}
			// only perform check if we already found the sphere once
			if (oldRadius > 0 && tc->search_tile==0) {
				tc->q2 = (float)fabs(oldRadius - tc->r) / (oldRadius + FLT_EPSILON);

				// additionally check for to big changes
                sphere_found = sphere_found && tc->q2 < tracker->settings.tracker_quality_t2;
			}

			// only if the quality is okay update the future ROI
			if (sphere_found) {
				// use adaptive color detection
				// only if 	1) the sphere has been found
				// AND		2) the UPDATE_RATE has passed
				// AND		3) the tracking-quality is high;
				int do_color_adaption = 0;
				long now = psmove_util_get_ticks();
                if (tracker->settings.color_update_rate > 0 && (now - tc->last_color_update) > tracker->settings.color_update_rate * 1000)
					do_color_adaption = 1;

                if (do_color_adaption &&
                    tc->q1 > tracker->settings.color_update_quality_t1 &&
                    tc->q2 < tracker->settings.color_update_quality_t2 &&
                    tc->q3 > tracker->settings.color_update_quality_t3)
                {
					// calculate the new estimated color (adaptive color estimation)
					CvScalar newColorHSV = th_rgb2hsv(th_bgr2rgb(cvAvg(tracker->frame, roi_m)));

                                        tc->eColorHSV = th_scalar_mul(th_scalar_add(tc->eColorHSV, newColorHSV), 0.5);

					tc->last_color_update = now;
					// CHECK if the current estimate is too far away from its original estimation
                    if (psmove_tracker_hsvcolor_diff(tc) > tracker->settings.color_adaption_quality_t) {
						tc->eColorHSV = tc->eFColorHSV;
						sphere_found = 0;
					}
				}

				// update the future roi box
				br.width = MAX(br.width, br.height) * 3;
				br.height = br.width;
				// find a suitable ROI level
				for (i = 0; i < ROIS; i++) {
					if (br.width > tracker->roiI[i]->width && br.height > tracker->roiI[i]->height)
						break;

                                        tc->roi_level = i;

					// update easy accessors
					roi_i = tracker->roiI[tc->roi_level];
					roi_m = tracker->roiM[tc->roi_level];
				}

				// assure that the roi is within the target image
				psmove_tracker_set_roi(tracker, tc, (int)(tc->x - roi_i->width / 2), (int)(tc->y - roi_i->height / 2),  roi_i->width, roi_i->height);
			}
		}
		cvClearMemStorage(tracker->storage);
		cvResetImageROI(tracker->frame);

		if (sphere_found) {
			//tc->search_tile = 0;
			// the sphere was found
			break;
		}else if(tc->roi_level>0){
			// the sphere was not found, increase the ROI and search again!
			tc->roi_x += roi_i->width / 2;
			tc->roi_y += roi_i->height / 2;

                        tc->roi_level = tc->roi_level - 1;

			// update easy accessors
			roi_i = tracker->roiI[tc->roi_level];
			roi_m = tracker->roiM[tc->roi_level];

			// assure that the roi is within the target image
			psmove_tracker_set_roi(tracker, tc, tc->roi_x -roi_i->width / 2, tc->roi_y - roi_i->height / 2, roi_i->width, roi_i->height);
		}else {
			int rx;
			int ry;
			// the sphere could not be found til a reasonable roi-level

            rx = tracker->settings.search_tile_width * (tc->search_tile %
                tracker->settings.search_tiles_horizontal);
            ry = tracker->settings.search_tile_height * (int)(tc->search_tile /
                tracker->settings.search_tiles_horizontal);
                        tc->search_tile = ((tc->search_tile + 2) %
                            tracker->settings.search_tiles_count);

			tc->roi_level=0;
			psmove_tracker_set_roi(tracker, tc, rx, ry, tracker->roiI[tc->roi_level]->width, tracker->roiI[tc->roi_level]->height);
			break;
		}
	}

	// remember if the sphere was found
	tc->is_tracked = sphere_found;
	return sphere_found;
}

int
psmove_tracker_update(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_val_if_fail(tracker->frame != NULL, 0);

    int spheres_found = 0;

    long started = psmove_util_get_ticks();

    TrackedController *tc;
    for_each_controller(tracker, tc) {
        if (move == NULL || tc->move == move) {
            spheres_found += psmove_tracker_update_controller(tracker, tc);
        }
    }

    tracker->duration = psmove_util_get_ticks() - started;

    return spheres_found;
}

int
psmove_tracker_get_position(PSMoveTracker *tracker, PSMove *move,
        float *x, float *y, float *radius)
{
    psmove_return_val_if_fail(tracker != NULL, 0);
    psmove_return_val_if_fail(move != NULL, 0);

    TrackedController *tc = psmove_tracker_find_controller(tracker, move);

    if (tc) {
        if (x) {
            *x = tc->x;
        }
        if (y) {
            *y = tc->y;
        }
        if (radius) {
            *radius = tc->r;
        }

        // TODO: return age of tracking values (if possible)
        return 1;
    }

    return 0;
}

void
psmove_tracker_get_size(PSMoveTracker *tracker,
        int *width, int *height)
{
    psmove_return_if_fail(tracker != NULL);
    psmove_return_if_fail(tracker->frame != NULL);

    *width = tracker->frame->width;
    *height = tracker->frame->height;
}

void
psmove_tracker_free(PSMoveTracker *tracker)
{
    psmove_return_if_fail(tracker != NULL);

    delete tracker;
}


TrackedController *
psmove_tracker_find_controller(PSMoveTracker *tracker, PSMove *move)
{
    psmove_return_val_if_fail(tracker != NULL, NULL);

    int i;
    for (i=0; i<PSMOVE_TRACKER_MAX_CONTROLLERS; i++) {
        if (tracker->controllers[i].move == move) {
            return &(tracker->controllers[i]);
        }

        // XXX: Assuming a "defragmented" list of controllers, we could stop our
        // search here if we arrive at a controller where move == NULL and admit
        // failure immediately. See the comment in psmove_tracker_disable() for
        // what we would have to do to always keep the list defragmented.
    }

    return NULL;
}

void
psmove_tracker_wait_for_frame(PSMoveTracker *tracker, IplImage **frame, int delay_ms)
{
    int elapsed_time_ms = 0;
    int step_ms = 10;

    while (elapsed_time_ms < delay_ms) {
        psmove_port_sleep_ms(step_ms);
        *frame = camera_control_query_frame(tracker->cc);
        elapsed_time_ms += step_ms;
    }
}

void psmove_tracker_get_diff(PSMoveTracker* tracker, PSMove* move,
        struct PSMove_RGBValue rgb, IplImage* on, IplImage* diff, int delay_ms,
        float dimming_factor)
{
    IplImage *frame = nullptr;

    // switch the LEDs ON and wait for the sphere to be fully lit
    rgb.r = (unsigned char)(rgb.r * dimming_factor);
    rgb.g = (unsigned char)(rgb.g * dimming_factor);
    rgb.b = (unsigned char)(rgb.b * dimming_factor);
    psmove_set_leds(move, rgb.r, rgb.g, rgb.b);
    psmove_update_leds(move);

    // take the first frame (sphere lit)
    psmove_tracker_wait_for_frame(tracker, &frame, delay_ms);
    cvCopy(frame, on, NULL);

    // switch the LEDs OFF and wait for the sphere to be off
    psmove_set_leds(move, 0, 0, 0);
    psmove_update_leds(move);

    // take the second frame (sphere off)
    psmove_tracker_wait_for_frame(tracker, &frame, delay_ms);

    // convert both to grayscale images
    IplImage* grey1 = cvCloneImage(diff);
    IplImage* grey2 = cvCloneImage(diff);
    cvCvtColor(frame, grey1, CV_BGR2GRAY);
    cvCvtColor(on, grey2, CV_BGR2GRAY);

    // calculate the diff of to images and save it in "diff"
    cvAbsDiff(grey1, grey2, diff);

    // clean up
    cvReleaseImage(&grey1);
    cvReleaseImage(&grey2);

    // threshold it to reduce image noise
    cvThreshold(diff, diff, tracker->settings.calibration_diff_t, 0xFF /* white */, CV_THRESH_BINARY);

    // use morphological operations to further remove noise
    cvErode(diff, diff, tracker->kCalib, 1);
    cvDilate(diff, diff, tracker->kCalib, 1);
}

void psmove_tracker_set_roi(PSMoveTracker* tracker, TrackedController* tc, int roi_x, int roi_y, int roi_width, int roi_height) {
	tc->roi_x = roi_x;
	tc->roi_y = roi_y;
	
	if (tc->roi_x < 0)
		tc->roi_x = 0;
	if (tc->roi_y < 0)
		tc->roi_y = 0;

	if (tc->roi_x + roi_width > tracker->frame->width)
		tc->roi_x = tracker->frame->width - roi_width;
	if (tc->roi_y + roi_height > tracker->frame->height)
		tc->roi_y = tracker->frame->height - roi_height;
}

void
psmove_tracker_annotate(PSMoveTracker *tracker, bool statusbar, bool rois)
{
	CvPoint p;
	IplImage* frame = tracker->frame;

    CvFont fontSmall = cvFont(0.8, 1);
    CvFont fontNormal = cvFont(1, 1);

    char text[256];
    int roi_w = 0;
    int roi_h = 0;

    // general statistics
    float avgLum = th_color_avg(cvAvg(frame, 0x0));

    if (tracker->duration) {
        tracker->debug_fps = (0.85f * tracker->debug_fps + 0.15f *
                (1000.0f / (float)tracker->duration));
    }

    if (statusbar) {
        cvRectangle(frame, cvPoint(0, 0), cvPoint(frame->width, 25), TH_COLOR_BLACK, CV_FILLED, 8, 0);
        sprintf(text, "fps:%.0f (%ld ms)", tracker->debug_fps, tracker->duration);
        cvPutText(frame, text, cvPoint(10, 20), &fontNormal, TH_COLOR_WHITE);
        sprintf(text, "avg(lum):%.0f", avgLum);
        cvPutText(frame, text, cvPoint(255, 20), &fontNormal, TH_COLOR_WHITE);
    }

    // Draw ROI rectangles first (below overlay text)
    TrackedController *tc;
    if (rois) {
        for_each_controller(tracker, tc) {
            roi_w = tracker->roiI[tc->roi_level]->width;
            roi_h = tracker->roiI[tc->roi_level]->height;

            CvScalar eColorBGR = th_rgb2bgr(th_hsv2rgb(tc->eColorHSV));

            if (tc->is_tracked) {
                cvRectangle(frame, cvPoint(tc->roi_x, tc->roi_y), cvPoint(tc->roi_x + roi_w, tc->roi_y + roi_h), eColorBGR, 3, 8, 0);
                cvRectangle(frame, cvPoint(tc->roi_x, tc->roi_y), cvPoint(tc->roi_x + roi_w, tc->roi_y + roi_h), TH_COLOR_WHITE, 1, 8, 0);
            } else {
                cvRectangle(frame, cvPoint(tc->roi_x, tc->roi_y), cvPoint(tc->roi_x + roi_w, tc->roi_y + roi_h), eColorBGR, 3, 8, 0);
            }
        }
    }

    // draw overlay text
    for_each_controller(tracker, tc) {
        if (tc->is_tracked) {
            // controller specific statistics
            p.x = (int)tc->x;
            p.y = (int)tc->y;
            roi_w = tracker->roiI[tc->roi_level]->width;
            roi_h = tracker->roiI[tc->roi_level]->height;

            CvScalar colorBGR = th_rgb2bgr(th_hsv2rgb(tc->eColorHSV));

            // Always use full brightness for the overlay color, independent of dimming
            double w = 255.0 / std::max(1.0, std::max(colorBGR.val[0], std::max(colorBGR.val[1], colorBGR.val[2])));
            colorBGR.val[0] *= w;
            colorBGR.val[1] *= w;
            colorBGR.val[2] *= w;

            double distance = psmove_tracker_distance_from_radius(tracker, tc->r);

            int x = tc->x;
            int y = tc->y + tc->r + 5;

            int textbox_h = 65;
            int textbox_w = 120;

            if (y + textbox_h >= frame->height) {
                y = tc->y - tc->r - 5 - textbox_h;
            }

            x -= textbox_w / 2;

            cvRectangle(frame, cvPoint(x, y), cvPoint(x + textbox_w, y + textbox_h), TH_COLOR_BLACK, CV_FILLED, 8, 0);

            CvScalar colorRGB = th_hsv2rgb(tc->eColorHSV);

            auto println = [&] (const std::string &text) {
                y += 10;
                cvPutText(frame, text.c_str(), cvPoint(x, y), &fontSmall, colorBGR);
            };

            println(format("camRGB:%02x,%02x,%02x", (int)colorRGB.val[0], (int)colorRGB.val[1], (int)colorRGB.val[2]));
            println(format("camHSV:%d,%d,%d", (int)tc->eColorHSV.val[0], (int)tc->eColorHSV.val[1], (int)tc->eColorHSV.val[2]));
            println(format("origHSV:%d,%d,%d", (int)tc->assignedHSV.val[0], (int)tc->assignedHSV.val[1], (int)tc->assignedHSV.val[2]));
            println(format("ROI:%dx%d", roi_w, roi_h));
            println(format("dist: %.2f cm", distance));
            println(format("radius: %.2f", tc->r));

            cvCircle(frame, p, (int)tc->r, TH_COLOR_WHITE, 1, 8, 0);
        }
    }
}

float psmove_tracker_hsvcolor_diff(TrackedController* tc) {
	float diff = 0;
	diff += (float)fabs(tc->eFColorHSV.val[0] - tc->eColorHSV.val[0]) * 1.0f; // diff of HUE is very important
	diff += (float)fabs(tc->eFColorHSV.val[1] - tc->eColorHSV.val[1]) * 0.5f; // saturation and value not so much
	diff += (float)fabs(tc->eFColorHSV.val[2] - tc->eColorHSV.val[2]) * 0.5f;
	return diff;
}

void psmove_tracker_biggest_contour(IplImage* img, CvMemStorage* stor, CvSeq** resContour, float* resSize) {
    CvSeq* contour;
    *resSize = 0;
    *resContour = 0;
    cvFindContours(img, stor, &contour, sizeof(CvContour), CV_RETR_LIST, CV_CHAIN_APPROX_SIMPLE, cvPoint(0, 0));

    for (; contour; contour = contour->h_next) {
        float f = (float)cvContourArea(contour, CV_WHOLE_SEQ, 0);
        if (f > *resSize) {
            *resSize = f;
            *resContour = contour;
        }
    }
}

void
psmove_tracker_estimate_circle_from_contour(CvSeq* cont, float *x, float *y, float* radius)
{
    psmove_return_if_fail(cont != NULL);
    psmove_return_if_fail(x != NULL && y != NULL && radius != NULL);

    int i, j;
    float d = 0;
    float cd = 0;
    CvPoint m1 = cvPoint( 0, 0 );
    CvPoint m2 = cvPoint( 0, 0 );
    CvPoint * p1;
    CvPoint * p2;
    int found = 0;

	int step = MAX(1,cont->total/20);

	// compare every two points of the contour (but not more than 20)
	// to find the most distant pair
	for (i = 0; i < cont->total; i += step) {
		p1 = (CvPoint*) cvGetSeqElem(cont, i);
		for (j = i + 1; j < cont->total; j += step) {
			p2 = (CvPoint*) cvGetSeqElem(cont, j);
			cd = (float)th_dist_squared(*p1,*p2);
			if (cd > d) {
				d = cd;
				m1 = *p1;
				m2 = *p2;
                                found = 1;
			}
		}
	}
    // calculate center of that pair
    if (found) {
            *x = 0.5f * (m1.x + m2.x);
            *y = 0.5f * (m1.y + m2.y);
    }
    // calcualte the radius
	*radius = (float)sqrt(d) / 2;
}

int
psmove_tracker_center_roi_on_controller(TrackedController* tc, PSMoveTracker* tracker, CvPoint *center)
{
    psmove_return_val_if_fail(tc != NULL, 0);
    psmove_return_val_if_fail(tracker != NULL, 0);
    psmove_return_val_if_fail(center != NULL, 0);

	CvScalar min = th_scalar_sub(tc->eColorHSV, tracker->rHSV);
        CvScalar max = th_scalar_add(tc->eColorHSV, tracker->rHSV);

	IplImage *roi_i = tracker->roiI[tc->roi_level];
	IplImage *roi_m = tracker->roiM[tc->roi_level];

	// cut out the roi!
	cvSetImageROI(tracker->frame, cvRect(tc->roi_x, tc->roi_y, roi_i->width, roi_i->height));
	cvCvtColor(tracker->frame, roi_i, CV_BGR2HSV);

	// apply color filter
	cvInRangeS(roi_i, min, max, roi_m);
	
	float sizeBest = 0;
	CvSeq* contourBest = NULL;
	psmove_tracker_biggest_contour(roi_m, tracker->storage, &contourBest, &sizeBest);
	if (contourBest) {
		cvSet(roi_m, TH_COLOR_BLACK, NULL);
		cvDrawContours(roi_m, contourBest, TH_COLOR_WHITE, TH_COLOR_WHITE, -1, CV_FILLED, 8, cvPoint(0, 0));
		// calucalte image-moments to estimate the better ROI center
		CvMoments mu;
		cvMoments(roi_m, &mu, 0);

        *center = cvPoint((int)(mu.m10 / mu.m00), (int)(mu.m01 / mu.m00));
		center->x += tc->roi_x - roi_m->width / 2;
		center->y += tc->roi_y - roi_m->height / 2;
	}
	cvClearMemStorage(tracker->storage);
	cvResetImageROI(tracker->frame);

        return (contourBest != NULL);
}

float
psmove_tracker_distance_from_radius(PSMoveTracker *tracker, float radius)
{
    psmove_return_val_if_fail(tracker != NULL, 0.);

    double height = (double)tracker->distance_parameters.height;
    double center = (double)tracker->distance_parameters.center;
    double hwhm = (double)tracker->distance_parameters.hwhm;
    double shape = (double)tracker->distance_parameters.shape;
    double x = (double)radius;

    /**
     * Pearson type VII distribution
     * http://fityk.nieto.pl/model.html
     **/
    double a = pow((x - center) / hwhm, 2.);
    double b = pow(2., 1. / shape) - 1.;
    double c = 1. + a * b;
    double distance = height / pow(c, shape);

    return (float)distance;
}

void
psmove_tracker_set_distance_parameters(PSMoveTracker *tracker,
        float height, float center, float hwhm, float shape)
{
    psmove_return_if_fail(tracker != NULL);

    tracker->distance_parameters.height = height;
    tracker->distance_parameters.center = center;
    tracker->distance_parameters.hwhm = hwhm;
    tracker->distance_parameters.shape = shape;
}


bool
psmove_tracker_color_is_used(PSMoveTracker *tracker, struct PSMove_RGBValue color)
{
    TrackedController *tc;
    for_each_controller(tracker, tc) {
        CvScalar rgb = th_hsv2rgb(tc->assignedHSV);

        if (int(rgb.val[0]) == color.r && int(rgb.val[1]) == color.g && int(rgb.val[2]) == color.b) {
            return true;
        }
    }

    return false;
}

const struct PSMoveCameraInfo *
psmove_tracker_get_camera_info(PSMoveTracker *tracker)
{
    return &tracker->camera_info;
}

int
psmove_tracker_hue_calibration(PSMoveTracker *tracker, PSMove *move)
{
    psmove_tracker_update_image(tracker);

    PSMOVE_VERIFY(tracker->frame != nullptr, "No frame from camera");
    PSMOVE_VERIFY(tracker->frame->depth == 8, "%d", tracker->frame->depth);

    CvSize size = cvGetSize(tracker->frame);

    // Switch off all other controllers for better measurements
    TrackedController *tc;
    for_each_controller(tracker, tc) {
        psmove_set_leds(tc->move, 0, 0, 0);
        psmove_update_leds(tc->move);
    }

    auto get_frame = [tracker] () -> IplImage * {
        IplImage *result = nullptr;
        psmove_tracker_wait_for_frame(tracker, &result, tracker->settings.calibration_blink_delay_ms);
        return result;
    };

    tracker->hue_calibration_info = psmove::tracker::hue_calibration_internal(tracker, move, size,
            get_frame, tracker->rHSV, tracker->kCalib);

    return tracker->hue_calibration_info.size();
}
