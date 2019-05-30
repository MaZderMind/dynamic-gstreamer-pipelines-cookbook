## Adding and Removing RTP-Sinks
This Example creates a Pipeline with an `audiotestsrc`, a `tee` and an internal `autoaudiosink`.
After 2, 4, and 6 seconds a Bin is added and linked to the `tee`-Element. The Bin contains all Elements necessary to
transmit the Audio to the Network as an RTP Stream. At 8, 10 and 12 Seconds one of the Bins is disabled and removed from
the Pipeline. After this, the Process starts over again.

```
gst-launch-1.0 udpsrc port=15000 !\
    application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 ! \
    rtpjitterbuffer latency=30 drop-on-latency=true ! \
    rtpL16depay ! \
    audio/x-raw,format=S16BE,rate=48000,channels=2 ! \
    audioconvert ! \
    audio/x-raw,format=S16LE,rate=48000,channels=2 ! \
    autoaudiosink
```

(!) Brings Pipeline to Paused state

You should read [Adding and Removing RTP-Sources](04-add-and-remove-network-source.md) before this, because important
Aspects that have been explained there are not repeated here.

This Experiment is very similar to [Adding and Removing RTP-Sources](04-add-and-remove-network-source.md), but the most
important differences are highlighted as such: 

 1. tee & allow-not-linked
 2. optional internal playback sink
 3. queue after tee
 4. network host & port
 5. blocking pad probe 
