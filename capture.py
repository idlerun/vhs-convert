#!/usr/bin/env python3
from subprocess import Popen, PIPE, STDOUT
import json
import argparse

parser = argparse.ArgumentParser(description='Video Capture')
parser.add_argument('--video_size', default="720x480", help='Video resolution setting for capture device')
parser.add_argument('--scale_to', default="640x480", help='Scale video to resolution')
parser.add_argument('--fps', default=29.97, type=float, help='Frames per second (float)')
parser.add_argument('--device', default="Conexant Polaris Video Capture", help='Capture device name')
parser.add_argument('--time', default="2:05:00", help='Capture time limit')
parser.add_argument('--crf', default=24, type=int, help='CRF setting')
parser.add_argument('--maxrate', default=2500, type=int, help='Maximum bitrate')
parser.add_argument('--out', required=True, help='Output file')
args = parser.parse_args()

cmd = [
  "ffmpeg",
  "-framerate", str(args.fps), 
  "-vsync", "1", 
  "-video_size", "720x480",
  "-f", "dshow",
  "-rtbufsize", "250000k",
  "-crossbar_video_input_pin_number", "1", 
  "-crossbar_audio_input_pin_number", "2",
  "-i", "video=" + args.device + ":audio=" + args.device,
  "-t", args.time,
  "-force_key_frames", ",".join(["00:00:%02d.000" % x for x in range(11)]),
  "-vf", "fps=" + str(args.fps) + ",yadif=0:0:0,hqdn3d=6:4:6:4,scale=" + args.scale_to,
  "-c:v", "libx264",
  "-preset", "medium",
  "-tune", "film", 
  "-profile:v", "main", 
  "-level", "3.1",
  "-pix_fmt", "yuv420p",
  "-crf", str(args.crf),
  "-maxrate", str(args.maxrate) + "k",
  "-bufsize", str(args.maxrate*2) + "k",
  "-af", "aresample=async=1000,highpass=200,lowpass=3500",
  "-c:a", "aac",
  "-b:a", "96k",
  "-strict", "-2",
  "-r", str(args.fps),
  args.out
]

print(cmd)
p = Popen(cmd, stdout=None, stderr=None)
#for line in p.stdout:
#  print("FFMPEG: " + line.decode('utf-8').rstrip())
exit = p.wait()
print("FFMPEG exit code " + str(exit))