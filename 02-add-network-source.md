explain goal and process

gst-launch-1.0 audiotestsrc freq=440 is-live=true ! audio/x-raw,format=S16BE,rate=48000,channels=2 ! rtpL16pay ! application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 ! udpsink host=127.0.0.1 port=10000

1. schedule on main-thread
2. all existing sources are live
3. udp-src is always live (ref doc)
4. lan vs. wlan vs. internet, jitter, ordering and gaps -- latency
   - 10ms Wifi
5. additional latency on the mixer
   - +5ms? +2ms? +1ms?
6. de-payload
7. be/le
8. bin
9. link inside bin
10. state
11. linking with caps
