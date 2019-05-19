explain goal and process

gst-launch-1.0 audiotestsrc freq=440 is-live=true ! audio/x-raw,format=S16BE,rate=48000,channels=2 ! rtpL16pay ! application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 ! udpsink host=127.0.0.1 port=10000

1. schedule on main-thread
2. all existing sources are live
3. udp-src is always live (ref doc)
4. lan vs. wlan vs. internet, jitter, ordering and gaps
5. de-payload
6. be/le
7. bin
8. link inside bin
9. state
10. linking with caps
