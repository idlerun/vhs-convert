Outlined here is the method I used for converting my VHS tapes to H264 files. To leave myself extra options open, I encoded them in a format that is also fully compatible with iTunes and most Apple devices.

## Setup
FFMPEG is doing all of the heavy lifting in this process. This program is available on all platforms.

I used Windows in my setup, so the commands will have to be changed slightly for other platforms. The required changes are those for device selection, as the _DirectShow_ video source is the Windows specific

Install FFMPEG and make sure to add it to your PATH.

## Device
A video capture device is required. I used the [August VGB100](http://www.amazon.ca/gp/product/B008F0SARC) which is available for $30 in Canada.

Install the device as normal. You won't need the conversion software that comes with the device, only the drivers.

## Prep-Work

### Device Identity (Windows)

Identify the name of the USB video capture device using the following command

```bash
ffmpeg -list_devices true -f dshow -i dummy
```
Sample Output:

```text
[dshow @ 0000025c7faba520] DirectShow video devices (some may be both video and audio devices)
[dshow @ 0000025c7faba520]  "Conexant Polaris Video Capture"
[dshow @ 0000025c7faba520]     Alternative name "@device_pnp_\\?\usb#vid_1f4d&amp;pid_0102&amp;mi_01#6&amp;1c48a6c&amp;0&amp;0001#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\{9b365890-165f-11d0-a195-0020afd156e4}"
[dshow @ 0000025c7faba520] DirectShow audio devices
[dshow @ 0000025c7faba520]  "Analog Audio In (USB2.0 Video Capture)"
[dshow @ 0000025c7faba520]     Alternative name "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\wave_{B93F2950-52BB-4B0D-86C2-25E92FAE012D}"
```

The video device here is `Conexant Polaris Video Capture`

### Device Options

Describe the options for the device:

```bash
ffmpeg -f dshow -list_options true -i video="Conexant Polaris Video Capture"
```

```text
[dshow @ 000002a2eb64a540] DirectShow video device options (from video devices)
[dshow @ 000002a2eb64a540]  Pin "Capture" (alternative pin name "2")
[dshow @ 000002a2eb64a540]   pixel_format=uyvy422  min s=88x72 fps=25 max s=720x576 fps=25
[dshow @ 000002a2eb64a540]   pixel_format=uyvy422  min s=80x60 fps=29.97 max s=720x480 fps=29.97
[dshow @ 000002a2eb64a540]   pixel_format=uyvy422  min s=88x72 fps=25 max s=720x576 fps=25
[dshow @ 000002a2eb64a540]   pixel_format=gray  min s=88x72 fps=25 max s=720x576 fps=25
[dshow @ 000002a2eb64a540]   pixel_format=uyvy422  min s=80x60 fps=29.97 max s=360x240 fps=29.97
[dshow @ 000002a2eb64a540]   pixel_format=gray  min s=80x60 fps=29.97 max s=360x240 fps=29.97
[dshow @ 000002a2eb64a540]   pixel_format=uyvy422  min s=88x72 fps=25 max s=360x288 fps=25
[dshow @ 000002a2eb64a540]   pixel_format=gray  min s=88x72 fps=25 max s=360x288 fps=25
[dshow @ 000002a2eb64a540]  Pin "Audio Out" (alternative pin name "3")
[dshow @ 000002a2eb64a540] Crossbar Switching Information for Conexant Polaris Video Capture:
[dshow @ 000002a2eb64a540]   Crossbar Output pin 0: "Video Decoder" related output pin: 1 current input pin: 0 compatible input pins: 0 1
[dshow @ 000002a2eb64a540]   Crossbar Output pin 1: "Audio Decoder" related output pin: 0 current input pin: 2 compatible input pins: 2
[dshow @ 000002a2eb64a540]   Crossbar Input pin 0 - "Video Composite" related input pin: 2
[dshow @ 000002a2eb64a540]   Crossbar Input pin 1 - "S-Video" related input pin: 2
[dshow @ 000002a2eb64a540]   Crossbar Input pin 2 - "Audio Line" related input pin: 0
```

For this USB device, the video device is *both* a video and audio device. This complicates the command as we need to select the correct crossbar input pins for audio and video. If the audio and video are two separate devices then the commands below can omit the crossbar pin selection.

* Video crossbar input is `Crossbar Input pin 0 - "Video Composite"`
* Audio crossbar input is `Crossbar Input pin 2 - "Audio Line"`

## Encoding Command

Here is the command used for converting the video

```bash
ffmpeg -framerate 25 -vsync 1 -video_size 720x576 -f dshow -rtbufsize 250000k \
  -crossbar_video_input_pin_number 0 -crossbar_audio_input_pin_number 2 \
  -i video="Conexant Polaris Video Capture":audio="Conexant Polaris Video Capture" \
  -t 4:10:00 -vf "fps=25,yadif=0:0:0,crop=w=702:h=576,hqdn3d=6:4:14:10,scale=640x480" \
  -c:v libx264 -preset medium -tune film -profile:v main -level 3.1 -pix_fmt yuv420p \
  -crf 25 -maxrate 1750k -bufsize 3500k -af "aresample=async=1000,highpass=200,lowpass=3500" \
  -c:a aac -b:a 96k -strict -2 -r 25 out.m4v
```

## Python Wrapper
To simplify usage, here is a simple Python wrapper for the ffmpeg capture command above. Modify it to customize the defaults to your preference or use command line arguments to configure.

[capture.py](https://github.com/idlerun/vhs-convert/blob/master/capture.py)

Usage:

```bash
./capture.py --out test.m4v
```

### Command Components

The arguments are broken down as follows:

#### Video Input Format
* `-framerate 25` Video framerate as 25 FPS
* `-vsync 1` Video synchronization method, "Frames will be duplicated and dropped to achieve exactly the requested constant frame rate." [vsync reference](https://ffmpeg.org/ffmpeg.html#Advanced-options)
* `-video_size 720x576` Video resolution. 720x576@25fps matches one of the video device option sets from above. In this case I am using PAL type VHS, so the 720x576@25 input is appropriate.

#### Video Input Device
* `-f dshow` DirectShow input format (Windows specific)
* `-rtbufsize 250000k` Real-Time input buffer size. Defines a 250MB buffer to be used as needed for storing a backlog of frames to process. This is needed if you are operating near the processing limit of your computer and need to handle spikes of processing work without losing frames.
* `-crossbar_video_input_pin_number 0` Video crossbar input pin from above
* `-crossbar_audio_input_pin_number 2` Audio crossbar input pin from above
* `-i video="Conexant Polaris Video Capture":audio="Conexant Polaris Video Capture"` Video and audio coming from the same video input device from above

#### Video Configuration
* `-t 4:10:00` Time after which to stop recording. VHS tapes will usually be marked as `E-60`, `E-120`, `E-240`. The number after E is the number of minutes on the tape. Do allow for an extra 10 minutes or so after that as they are often slightly longer.Set the length to stop the recording at. This can be set based on the type of VHS being converted. Generally tapes will have an indicator on them somewhere as E-60, E-120, E-240. When in doubt, set the time to 4:10:00 and stop the recording by pressing `Q` when the VHS player reaches the end of the tape.

#### Video Filtering
* `-vf` Start video filter definitions (comma separated, ordered processing)
* `fps=25` Extra pedantic conversion to 25FPS, adding here seems to help avoid spammy console warnings saying `Past duration X.XX is too large`
* `yadif=0:0:0` Deinterlace the video input. [YADIF filter reference](https://ffmpeg.org/ffmpeg-filters.html#yadif-1)
* `crop=w=702:h=576` Crop off the edges of the video to the correct 4:3 aspect ratio [PAL AR](http://www.ict4e.net/wiki_mirror/index.php?page=Tutorials/Video/Pixel_Aspect_Ratio). [Crop filter Reference](https://ffmpeg.org/ffmpeg-filters.html#crop)
* `hqdn3d=6:4:14:10` Remove noise from the video (also improves compression). First two parameters are spatial strength, second two are temporal strength. [Hqdn3d filter reference](https://ffmpeg.org/ffmpeg-filters.html#hqdn3d-1)
* `scale=640x480` resize down to 640x480 which is a more standard 4:3 AR resolution. [Scale filter reference](https://ffmpeg.org/ffmpeg-filters.html#scale) 

#### Video Compressor
* `-c:v libx264` Use x264 to generate h264 encoded video
* `-preset medium` Preset defines how hard the engine will work to compress video. The useful values in order `veryslow`, `slower`, `slow`, `medium`, `fast`, `faster`, `veryfast`. Use the *slowest* setting that your computer can keep up with without maxing out your processor. If your computer can't keep up, you will start getting errors **"real-time buffer [...] too full or near too full (78% of size: 250000000 [rtbufsize parameter])! frame dropped!"**.
* `-tune film` Tuning for the x264 engine. "*film* is for live-action content: anything shot on a camera, as opposed to cell animation or computer generated text/charts" [tune options](http://superuser.com/a/564404)
* `-profile:v main -level 3.1` Set the H264 compatibility settings. These values will support almost all devices including: iPad (all versions), Apple TV 2 and later, and iPhone 4 and later [Apple reference](https://developer.apple.com/library/mac/documentation/NetworkingInternet/Conceptual/StreamingMediaGuide/UsingHTTPLiveStreaming/UsingHTTPLiveStreaming.html#//apple_ref/doc/uid/TP40008332-CH102-SW8)
* `-pix_fmt yuv420p` Required pixel format for maximum compatibility
* `-crf 25` Constant quality setting for video. Lower number is higher quality. *Sane range* is 18-28. Uses whatever bitrate is required to retain a generally constant quality to the video. [encoder reference](https://trac.ffmpeg.org/wiki/Encode/H.264)
* `-maxrate 1750k` Set a maximum bitrate for the output video. This will override the crf for extremely noisy content to keep the file from getting too large.
* `-bufsize 3500k` Should be used alongside `maxrate`. Effectively determines how often the `maxrate` is verified (3500k/1750kps) = every 2 seconds

#### Audio Filtering
* `-af` Start audio filter definitions
* `aresample=async=1000` "Stretch/squeeze samples to the given timestamps, with a maximum of 1000 samples per second compensation" [aresample filter reference](https://ffmpeg.org/ffmpeg-filters.html#aresample-1)
* `highpass=200,lowpass=3500` Drop audio outside of the [human voice range](https://en.wikipedia.org/wiki/Voice_frequency) to remove noise.

#### Audio Compressor
* `-c:a aac` Use the AAC audio codec which is highly compatible (including Apple devices)
* `-b:a 96k` Use 96 kbps audio bitrate. This is more than enough for the audio quality stored on VHS (especially after the frequency filtering above)
* `-strict -2` Required on some platforms to enable the AAC codec

#### Output
* `-r 25` Force output framerate as constant 25 FPS
* `out.m4v` Set the output file name. m4v is the expected extension for iTunes. mp4 is also an appropriate extension.


##### Alternate Output (With Display)
It may be helpful to see the output as it is recording. Note that this will require extra processing power and may require a faster x264 preset value.
Replace `out.m4v` with

```bash
-f tee -map 0:v -map 0:a "out.m4v|[f=mpegts]udp://localhost:10001"
```

This will simultaneously write to out.m4v and send all video over UDP to port 10001. Then we can monitor the video output on that port with ffplay (which comes with ffmpeg)

```bash
ffplay -an -fast -framedrop -noinfbuf -vf scale=w=in_w/2:h=in_h/2 -loglevel panic \
  -i udp://localhost:10001?listen
```

Note that `-an` disables playing out audio, and the input is scaled down by half for display.

**DANGER**
Unlike the normal out.m4v output, this command will *NOT* prompt before overwriting an output file. Extra care must be taken to avoid overwriting your output accidentally.

### Trimming
If there is excessive content after the recorded video ends, it can be safely trimmed off without any need to re-encode the video.

Open the video in a player such as VLC and find the start and end of the video stream. Then trim the video as follows:

```bash
ffmpeg -ss 10 -i out.m4v -c copy -to 1:10:00 out-trimmed.m4v
```

* `-ss 10` Seek input to 10 seconds. Unfortunately without re-encoding the video, the start of the video cannot be trimmed correctly between key-frames, `ss` should find the closest key-frame to seek to and start there. Leave this parameter off entirely if there is an acceptably small amount of wasted video at the start
* `-i out.m4v` Read from the previously written output file
* `-c copy` Use the `copy` codec for both audio and video, should process even large videos extremely quickly, since no re-encoding is being done
* `-to 1:10:00` End the video copy at a specific time marker, everything after this point will be trimmed off
* `out-trimmed.m4v` The output file to write to
