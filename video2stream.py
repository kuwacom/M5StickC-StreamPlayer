import argparse
import cv2
import socket
import time
import numpy as np
import pyautogui

FRAME_START_DRAW = 0xA1
PIXEL_DRAW = 0xA2
SET_STREAM_SIZE_RATIO = 0xA3

def videoToStream(host, port, videoPath, packetInterval, streamSizeRatio, dispWidth, dispHeight, skipCount):
    dispWidth = int(dispWidth / streamSizeRatio)
    dispHeight = int(dispHeight / streamSizeRatio)

    # UDPソケット設定
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpAddress = (host, port)

    cap = cv2.VideoCapture(videoPath)

    if not cap.isOpened():
        print("動画の読み込みに失敗しました。")
        exit()

    frameCount = 0
    totalFrameCount = 0

    # 実際に送る映像のサイズ倍率を設定
    udpSocket.sendto(bytes([SET_STREAM_SIZE_RATIO, streamSizeRatio]), udpAddress)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            totalFrameCount += 1
            if skipCount > frameCount:
                frameCount += 1    
                continue
            frameCount = 0

            # フレームリサイズ
            resizedFrame = cv2.resize(frame, (dispWidth, dispHeight))
            rgbFrame = cv2.cvtColor(resizedFrame, cv2.COLOR_BGR2RGB)

            # プレビューを表示
            cv2.imshow("Preview", frame)
            print(f"Frame: {totalFrameCount}")
            
            if cv2.waitKey(1) & 0xFF == 27:
                break

            # 1ラインずつ送信
            for y in range(dispHeight):
                for x in range(dispWidth):
                    if (y == 0 and x == 0):
                        rowData = [FRAME_START_DRAW] # フレームの始まりは FRAME_START_DRAW
                    elif(x == 0):
                        rowData = [PIXEL_DRAW] # 行の始まりは PIXEL_DRAW
                    r, g, b = rgbFrame[y, x]
                    rowData.extend([r, g, b]) # 1ピクセルずつRGBを追加
                # ラインをUDPで送信
                udpSocket.sendto(bytearray(rowData), udpAddress)
                # 早すぎるとパケロスして死ぬ
                time.sleep(packetInterval / 1000)

    finally:
        udpSocket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="動画をネットワーク経由で送信")
    parser.add_argument("host", help="ホスト名またはIPアドレス")
    parser.add_argument("port", type=int, help="UDPポート番号")
    parser.add_argument("videoPath", help="動画ファイルのパス")
    parser.add_argument("-ssr", "--streamSizeRatio", type=int, default=2, help="ストリームで送信する映像データのサイズ倍率（デフォルト: 2）")
    parser.add_argument("-dw", "--dispWidth", type=int, default=160, help="ディスプレイの幅（デフォルト: 160）")
    parser.add_argument("-dh", "--dispHeight", type=int, default=80, help="ディスプレイの高さ（デフォルト: 80）")
    parser.add_argument("-s", "--skipCount", type=int, default=0, help="スキップするフレーム数（デフォルト: 0）")
    parser.add_argument("-pi", "--packetInterval", type=float, default=40, help="パケット通信の間隔[ms]（デフォルト: 40）")

    args = parser.parse_args()

    # 動画を指定のホストに送信
    videoToStream(args.host, args.port, args.videoPath, args.packetInterval, args.streamSizeRatio, args.dispWidth, args.dispHeight, args.skipCount)
