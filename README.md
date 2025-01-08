Tensorflow install for Raspberry pi:
pip install https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0-rc2/tensorflow-2.4.0rc2-cp37-none-linux_armv7l.whl
On other distro use 'requirements.txt'

Config file in /lib/config/config.json:

"version": "0.0",
"heartbeat": 5, //interval of heartbeat messages in seconds
"backend": {
"ip": "192.168.1.102",
"port": 5000
},
"camera": {
"source": "./assets/simulation_video.mp4", // default value is 0 (webcam). Use path "/like/this.mp4" to stream a video file.
"width": 1280,
"height": 720,
"decrease": 2 // each frame dimensions devided by this value. Can be float.
},
"cnn": {
"classes": [ // Possible outputs of netural network. Has to be the same as the networks defaults.
"Uncertain",
"Present",
"Missing"
],
"false_frames": 3, // This many predictions has to be same in a row to accept
"threshold_max": 99,
"threshold_min": 96.1,
"max_size": 1000000000 // max size of saved images in kilobytes. Use -1 to turn off data collecting
}

Build docker with this command:
docker build -t rpi .

Export image:
docker save rpi:latest > rpi.tar

Load image:
docker load --input rpi.tar

Run docker:
docker run --rm -p 3000:3000 --device=/dev/video0:/dev/video0 rpi
