#include "Arduino.h"
#include "esp_camera.h"
#include "esp_http_server.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "esp32-hal-ledc.h"
#include "sdkconfig.h"

#if defined(ARDUINO_ARCH_ESP32) && defined(CONFIG_ARDUHAL_ESP_LOG)
#include "esp32-hal-log.h"
#endif

#if defined(LED_GPIO_NUM)
#define CONFIG_LED_MAX_INTENSITY 255
static int led_duty = 0;
static bool is_streaming = false;

static void enable_led(bool en)
{
    int duty = en ? led_duty : 0;
    if (en && is_streaming && duty > CONFIG_LED_MAX_INTENSITY)
    {
        duty = CONFIG_LED_MAX_INTENSITY;
    }
    ledcWrite(LED_GPIO_NUM, duty);
}
#endif

#define PART_BOUNDARY "123456789000000000000987654321"
static const char *STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char *STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char *STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\nX-Timestamp: %ld.%06ld\r\n\r\n";

static httpd_handle_t camera_httpd = NULL;

static esp_err_t stream_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL;
    struct timeval ts;
    esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
    size_t jpg_buf_len = 0;
    uint8_t *jpg_buf = NULL;
    char part_buf[128];

    if (res != ESP_OK)
    {
        return res;
    }

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

#if defined(LED_GPIO_NUM)
    is_streaming = true;
    enable_led(true);
#endif

    while (res == ESP_OK)
    {
        fb = esp_camera_fb_get();
        if (!fb)
        {
            log_e("Camera capture failed");
            res = ESP_FAIL;
            break;
        }

        ts.tv_sec = fb->timestamp.tv_sec;
        ts.tv_usec = fb->timestamp.tv_usec;

        if (fb->format == PIXFORMAT_JPEG)
        {
            jpg_buf = fb->buf;
            jpg_buf_len = fb->len;
        }
        else
        {
            bool jpeg_converted = frame2jpg(fb, 80, &jpg_buf, &jpg_buf_len);
            esp_camera_fb_return(fb);
            fb = NULL;
            if (!jpeg_converted)
            {
                log_e("JPEG conversion failed");
                res = ESP_FAIL;
                break;
            }
        }

        res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
        if (res == ESP_OK)
        {
            size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART, jpg_buf_len, (long)ts.tv_sec, (long)ts.tv_usec);
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        if (res == ESP_OK)
        {
            res = httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_buf_len);
        }

        if (fb)
        {
            esp_camera_fb_return(fb);
            fb = NULL;
            jpg_buf = NULL;
        }
        else if (jpg_buf)
        {
            free(jpg_buf);
            jpg_buf = NULL;
        }
    }

#if defined(LED_GPIO_NUM)
    is_streaming = false;
    enable_led(false);
#endif

    return res;
}

void startCameraServer()
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_uri_handlers = 2;

    httpd_uri_t stream_uri = {
        .uri = "/stream",
        .method = HTTP_GET,
        .handler = stream_handler,
        .user_ctx = NULL
#ifdef CONFIG_HTTPD_WS_SUPPORT
        ,
        .is_websocket = true,
        .handle_ws_control_frames = false,
        .supported_subprotocol = NULL
#endif
    };

    log_i("Starting stream server on port: '%u'", config.server_port);
    if (httpd_start(&camera_httpd, &config) == ESP_OK)
    {
        httpd_register_uri_handler(camera_httpd, &stream_uri);
    }
}

void setupLedFlash()
{
#if defined(LED_GPIO_NUM)
    ledcAttach(LED_GPIO_NUM, 5000, 8);
#else
    log_i("LED flash is disabled -> LED_GPIO_NUM undefined");
#endif
}
