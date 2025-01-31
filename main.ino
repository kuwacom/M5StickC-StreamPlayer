#include <M5StickC.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secret.h"

#define FRAME_START_DRAW 0xA1
#define PIXEL_DRAW 0xA2
#define SET_STREAM_SIZE_RATIO 0xA3

// ディスプレイサイズ
#define DISP_WIDTH 160
#define DISP_HEIGHT 80

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;
const int udpPort = 12345;

WiFiUDP udp;
uint8_t packetBuffer[512];
int displayX = 0, displayY = 0, x = 0, y = 0;
uint8_t bufferType, r, g, b; // ピクセルのRGBデータ
uint8_t streamSizeRatio = 1;

void setup()
{
    M5.begin();

    M5.Lcd.setRotation(3);
    M5.Lcd.setTextFont(2);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(0, 0);

    // WiFi接続
    WiFi.begin(ssid, password);
    M5.Lcd.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        M5.Lcd.print(".");
    }
    M5.Lcd.setTextColor(GREEN, BLACK);
    M5.Lcd.println("\nWiFi Connected!!");
    M5.Lcd.println(WiFi.localIP()); // IPアドレスを表示

    delay(2000);
    udp.begin(udpPort);
}

void loop()
{
    // 受信したUDPデータを確認
    int packetSize = udp.parsePacket();
    if (packetSize >= 2)
    {
        udp.read(packetBuffer, packetSize);
        bufferType = packetBuffer[0];

        if (bufferType == SET_STREAM_SIZE_RATIO)
        {
            streamSizeRatio = packetBuffer[1];
            return;
        }

        // 受け取ったモードが描画モードだったら
        if (bufferType == FRAME_START_DRAW || bufferType == PIXEL_DRAW)
        {
            if (bufferType == FRAME_START_DRAW)
            {
                y = displayY = 0;
            }

            // for (int x = 0; displayX <= DISP_WIDTH; x++)
            while (displayX <= DISP_WIDTH)
            {
                r = packetBuffer[x * 3 + 1];
                g = packetBuffer[x * 3 + 2];
                b = packetBuffer[x * 3 + 3];

                // 受信したRGB値でピクセルを表示
                for (int i = 0; i < streamSizeRatio; i++)
                    for (int j = 0; j < streamSizeRatio; j++)
                        M5.Lcd.drawPixel(displayX + i, displayY + j, M5.Lcd.color565(r, g, b));

                x++;
                displayX += streamSizeRatio;
            }

            // 次のピクセル座標へ移動
            x = displayX = 0;
            y++;
            displayY += streamSizeRatio;
            if (displayY >= DISP_HEIGHT)
            {
                y = displayY = 0;
            }
        }
    }
}