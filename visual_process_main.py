# -*- coding: utf-8 -*-
"""visual_process_main.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1waf9eHojx4ntcl3_Hwc6HovbNIIVkyz4
"""

#準備
import cv2
import pandas as pd
import numpy as np
import time
from calc_onset import onset_consider_volume
from calc_onset import add_another_timing
from performer_detection import yolo_detection, feature_extraction
from visual_expression import zoom_frames, split_frames, line_frames, put_lyric


def main():
  #default_setting
  cap = cv2.VideoCapture("./video/yumeno_test.mp4")#動画
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))#横幅
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))#縦幅
  size = (width, height)#(横幅, 縦幅)
  fps = float(cap.get(cv2.CAP_PROP_FPS))#fps
  totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))#フレーム総数
  # 出力フォーマット
  fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
  video = cv2.VideoWriter("./output/out_video_test.mp4", fourcc, fps, (width, height))#出力動画
  #正解データ
  yumeno_lyric_test = [["夢ってかっこよかったよな", 20.28, 24.13], \
                      ["みんな忘れちゃったのかい", 25.20, 28.09], \
                      ["忘れちゃったのかい", 28.23, 31.01], \
                      ["あの頃何になりたかったかなんて", 31.14 , 34.27], \
                      ["今じゃただの笑い話だよな", 36.08, 40.17], \
                      ["言いたいことも言えないまま", 42.04, 44.11],\
                      ["現実逃避だけが上手くなって", 44.20, 47.08], \
                      ["言葉選びを間違えて", 47.26, 51.11], \
                      ["また人を傷つけて", 52.16, 56.20], \
                      ["無邪気でいいねっていわれたよ", 57.01, 62.25], \
                      ["いつも本気で思ってた", 83.29, 86.04], \
                      ["あなたのことも夢の続きも", 86.17, 89.01], \
                      ["いつかわかると思ってた", 89.08, 91.12], \
                      ["涙の訳も生きることの意味も", 91.26, 94.10]]
  vocal_time_start = []
  for i in range(len(yumeno_lyric_test)):
    vocal_time_start.append(yumeno_lyric_test[i][1])

  #メイン処理
  switch_visual_timing = onset_consider_volume("audio/yumeno_test.wav")
  switch_visual_timing = add_another_timing(switch_visual_timing, vocal_time_start)
  frame_count = 0
  start_time = time.time()
  frames = []
  times = []
  #現在のそれぞれの演者の動作量
  df_performer_movement = pd.DataFrame([], columns=["xmin", "ymin", "xmax", "ymax", "movement", "visual_express"])
  #前のフレーム情報
  frame_before = None #1つ前のフレーム
  df_objects_performer_before = pd.DataFrame([], [])#1つ前の上手く人物認識できたフレーム情報
  df_performer_movement_before = pd.DataFrame([], columns=["xmin", "ymin", "xmax", "ymax", "movement", "visual_express"])#１つ前のフレームでのそれぞれの演者の動作量
  #実行
  while True:
    # 画像を取得
    ret, frame = cap.read()
    frame_original = frame
    # 再生が終了したらループを抜ける
    if ret == False:
      write_frames(frames, times)
      break
    #-------処理--------
    #演者認識
    df_objects_performer = yolo_detection(frame, df_objects_performer_before)
    #動体検知
    df_performer_movement = feature_extraction(frame, frame_before, df_objects_performer, df_objects_performer_before, df_performer_movement)
    #動体検知による映像表現、logのリセット
    if len(switch_visual_timing) > 0:
      if switch_visual_timing[0] < frame_count/fps:
        if df_performer_movement_before.empty:
          df_performer_movement_before = df_performer_movement.copy()
          df_performer_movement = pd.DataFrame([], columns=["xmin", "ymin", "xmax", "ymax", "movement"])
        else:
          print("success")
          #映像表現
          for row in df_performer_movement.itertuples():
            if row.Index in df_performer_movement_before.index:
              movement = row.movement
              movement_before = df_performer_movement_before.movement[row.Index]
              movement_per_frame = movement / len(frames)
              movement_before_per_frame = movement_before / len(frames)
              movement_ratio_per_frame = movement_per_frame / movement_before_per_frame
              if movement_ratio_per_frame > 2.0:
                df_performer_movement.loc[row.Index, "visual_express"] = int(2)
              elif movement_ratio_per_frame > 1.2:
                df_performer_movement.loc[row.Index, "visual_express"] = int(1)
              else:
                df_performer_movement.loc[row.Index, "visual_express"] = int(0)
            else:
              df_performer_movement.loc[row.Index, "visual_express"] = int(0)
          if not df_performer_movement[df_performer_movement['visual_express'] == 2].empty:
            df_performer_movement_2 = df_performer_movement[df_performer_movement['visual_express'] == 2]
            df_performer_movement_2 = df_performer_movement_2.sort_values('movement')
            df_performer_movement_2 = df_performer_movement_2.reset_index()
            if len(df_performer_movement_2) == len(df_performer_movement):
              #画面分割
              frames = split_frames(frames, df_performer_movement)
              print("split")
              #
            else:
              line_xmin = df_performer_movement_2.loc[0, "xmin"]
              line_xmax = df_performer_movement_2.loc[0, "xmax"]
              line_ymin = df_performer_movement_2.loc[0, "ymin"]
              line_ymax = df_performer_movement_2.loc[0, "ymax"]
              #方向線
              frames = zoom_frames(frames, line_xmin, line_xmax, line_ymin, line_ymax)
              frames = line_frames(frames)
              print("line")
          elif not df_performer_movement[df_performer_movement['visual_express'] == 1].empty:
            df_performer_movement_1 = df_performer_movement[df_performer_movement['visual_express'] == 1]
            df_performer_movement_1 = df_performer_movement_1.sort_values('movement')
            df_performer_movement_1 = df_performer_movement_1.reset_index()
            zoom_xmin = df_performer_movement_1.loc[0, "xmin"]
            zoom_xmax = df_performer_movement_1.loc[0, "xmax"]
            zoom_ymin = df_performer_movement_1.loc[0, "ymin"]
            zoom_ymax = df_performer_movement_1.loc[0, "ymax"]
            #ズーム
            frames = zoom_frames(frames, zoom_xmin, zoom_xmax, zoom_ymin, zoom_ymax)
            print("zoom")
          elif len(df_performer_movement[df_performer_movement['visual_express'] == 0]) == len(df_performer_movement):
            print("None")
          df_performer_movement_before = df_performer_movement.copy()
          df_performer_movement = pd.DataFrame([], columns=["xmin", "ymin", "xmax", "ymax", "movement"])
          switch_visual_timing.pop(0)
        #歌詞の付与
        frames = put_lyric(frames, times, yumeno_lyric_test)
        write_frames(frames, times)
        frames.clear()
        times.clear()

    #フレーム情報の保存
    frames.append(frame)
    times.append(frame_count/fps)
    df_objects_performer_before = df_objects_performer
    #--------------------

    print(frame_count/totalFrames*100)
    frame_before = frame_original
    frame_count+=1

  cap.release()
  video.release()
  print("success!")

#フレームの書き込み
def write_frames(frames:list, times:list) -> None:
  global start_time
  global video
  global cap
  for i in range(len(frames)):
    frame = frames[i]
    time = times[i]
    video.write(frame)

    #ウィンドウでの再生速度を元動画と合わせる
    elapsed = (time) * 1000  # msec
    play_time = int(cap.get(cv2.CAP_PROP_POS_MSEC))
    sleep = max(1, int(play_time - elapsed))
    if cv2.waitKey(sleep) & 0xFF == ord("q"):
      break

if __name__ == "__main__":
  main()