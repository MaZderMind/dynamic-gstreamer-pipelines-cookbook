# Adding RTP Network-Sources
→ [Sourcecode](02-add-network-source.py)

This Example creates a Pipeline like this:

```
audiotestsrc is-live=true ! audiomixer ! autoaudiosink
```

After 2 Seconds it adds a RTP-Receiving-Bin like this to the Pipeline:
```
udpsrc port=10000 !
  application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 !
  rtpjitterbuffer latency=… !
  rtpL16depay !
  audio/x-raw,format=S16BE,rate=48000,channels=2 !
  audioconvert !
  audio/x-raw,format=S16LE,rate=48000,channels=2 !
  autoaudiosink
```

After 4 and 6 seconds (from the start) another Receiving-Sink on Port `10001` and `10002` is added.

The Example installs Pad-Probes in after interesting stages, which log the PTS-Timestamps
of the Buffers flowing through the Elements' Pads.

After the start you can hear a a low volume 110 Hz Hum on the Speaker. On the Console you can see the Buffers being
generated in real time, because the `audiotestsrc` is forced to be a live source with the `is-live` property.
Without that, it would run as fast as the sink allows it to. 

After 2 Seconds the RTP Receiving bin is added, but because there is no RTP Source yet, nothing changes.
You can hear the 110 Hz Background Hum continuing without interruption. On the Console you can see that the `udpsrc`
has been added and the new elements switched through all States and are now `RUNNING` , but it does not generate
buffers yet because nothing is received on the UDP Port .

You can now start a RDP-Source on the Same or a different Computer on the Network:
```
gst-launch-1.0 audiotestsrc freq=440 volume=0.5 is-live=true ! \
  audio/x-raw,format=S16BE,rate=48000,channels=2 ! \
  rtpL16pay ! \
  application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 ! \
  udpsink host=… port=10000
```

On the speaker you can now hear both tones being mixed together and played back.
On the Console you can see the Timestamps of the `udpsrc` starting close the the timestamps currently mixed by
the mixer, because Elements of type `udpsrc` are always live.

You now start an stop the RDP Source. The Background-Hum will continue and your added RDP Source will immediately start
to mix with it again, as soon as you start it. The `rtpjitterbuffer`-Element can detect the loss of the source signal
and re-start the timing correction when the signals starts again.

The most important Lines have been marked as such:

 1. We schedule the execution on the GLib Event-Loop by using `Glib.idle_add`. On the Console you can see, that the
    Sequence runs in its own `Sequence`-Thread but the second testsrc is actually added from the `MainThread`.

    It seems that this exact example also works without this, because some of the Methods are Thread-Safe by
    Documentation (ie. [Bin.add](https://lazka.github.io/pgi-docs/#Gst-1.0/classes/Bin.html#Gst.Bin.add)) and some are
    by luck (ie [Gobject.Object.set_property](https://lazka.github.io/pgi-docs/#GObject-2.0/classes/Object.html#GObject.Object.set_property)),
    but not following this pattern can lead to unexpected and hard to find issues.

    From the console you can also see, that the Pad-Probes are called synchronously from their respective Elements' 
    Streaming-Threads (Shown as `Dummy-[n]`).

 2. Forcing the `audiotestsrc` to be a Live-Source makes it produce Buffers with timestamps starting at the current
    Running-Time of the Pipeline. A Non-Live-Source would start ad 0:00:00 and run faster then the other sources,
    until it would have caught up to the current Running-Time.
 
 3. The `udpsrc` added is always live (see [Documentation](https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good/html/gst-plugins-good-plugins-udpsrc.html#gst-plugins-good-plugins-udpsrc.description]))

 4. Our RTP-Packets on the Network are not obviously not delivered instantly. The Source on the Source-Pipeline takes the
    Running-Time of the Source-Pipeline and stamps the generated Buffers into it. This timestamp is encoded into the 
    RTP-Packets and given to the Network-Stack.
 
    The Network-Stack on both sided, Switches, Routers, WLan APs and other Network Equipment all have Buffers which delay 
    our RTP Packets. Furthermore the exact amount of Delay is different for each and every RTP Packet.
    
    To circumvent this Jitter, an `rtpjitterbuffer` is added to the Pipeline and configured with the maximal allowed Jitter.
    It is also instructed to drop all late Packets. This will make a too low configured Latency obvious.
    
    The Jitter-Buffer will artificially delay each incoming Buffer, so that it plays back at its Timestamp plus the 
    configured Latency. For example given a configured Latency of **20ms**, a Buffer with a Timestamp of **t=1000ms** 
    will be played back at **t=1020ms**, no matter if it has been received at **t=1001ms**, **t=1005ms**, **t=1010ms** 
    or **t=10019ms**.
    
    So with a configured Latency of **20ms** Your Network (including the Network-Stacks on both ends) is allowed to 
    Jitter up to that amount back and forth, without the Receiving-Side starting to drop Packets.
    
    In my tests I found **30ms** to be a good start for Devices talking across multiple Switches and a Wifi-Access-Point
    under Linux. When all Devices are on a non-crowded GBit Ethernet Link **10ms** should be fine too.
    Across the Internet a Value of **200ms** or upwards might be required.

    Under MacOS I needed to go to **100ms** on Wifi. Your mileage may vary.

 5. The Audiomixer has, apart from its obvious job of combining Audio-Samples, the task of syncing up incoming Streams
    and only mixing samples that are meant to be played back at the same time. When a least one of the sources linked to
    an `audiomixer` Element is a live-source, the Audiomixer itself is live and generates buffers stamped with the current
    running time of the Pipeline.
    
    Obviously in our Situation it can't mix the Samples stamped for **t=1000ms* at **t=1000ms** because they will still
    be waiting in the Jitter-Buffer. When going to `PLAYING` the Audiomixer queries all its sources for their latency and
    configured its own latency accordingly. In a dynamic Pipeline like this, the Source of Latency is not yet present when
    the Pipeline initially goes to `PLAYING`, so we need to configure the Audio-Mixers latency beforehand to the same or
    a higher value, then we configured the `rtpjitterbuffer` to buffer our RTP-Packets.
 
 6. GStreamer comes with a metric ton of [RTP de/payloader elements](https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-plugin-rtp.html).
    This example chose L16 (specified in [RFC 3551](https://tools.ietf.org/html/rfc3551)) which encodes Audio as Uncompressed
    16bit PCM in Network-Byte-Order (Big Endian).
    
    To enable Compressed Transfer a decoder-Element (ie `opusdec` can be added together with the matching depayloader,
    ie. `rtpopuspay`).

 7. While not all Audio-Handling Elements are capable of working on Big Endian PCM (especially `autoaudiosink`, `level`,
    `volume` and `wavenc` aren't), all can handle Little Endian PCM. Furthermore some elements like the Audiomixer can
    will silently convert the Big Endian Samples to Little Endian, but every `audiomixer`-Element will do this for itself.
    
    To avoid these problem the complete main pipeline runs in Little Endian mode and the Buffers received from the Network
    are converted from Big to Little Endian before they are passed onto the audiomixer.

 8. To Simplify State-Handling, all Elements are placed into a Bin (a Cluster of Elements) which maintains state for all
    its Child-Elements.

 9. When Elements from Inside a Bin are linked with Elements outside the Bin or in another Bin, so called Ghost-Pads are
    created at the Boundary of the Bin. These Ghost-Pads can be actively managed by the Bin (for Details see the 
    [Documentation on Ghost Pads](https://gstreamer.freedesktop.org/documentation/application-development/basics/pads.html?gi-language=c#ghost-pads))
    but Ghost Pads are also automatically created, when a Cross-Bin-Link is performed, like in this example.

10. The Bin does not automatically take over its parent state. Also, not all Elements in a Pipeline have to have the
    same state. In this case the new Bin and all its Elements starts in `NULL` state and is added as such to the Pipeline.
    Once it is added, the Bins state is synced to the pipeline which in turn propagate this State-Change to all its Child-
    Elements.

11. At some points in the Pipeline multiple Media-Types can be processed by both Elements participating being linked together
    and especially in a dynamic pipeline not all requirements to these media-types are known at pipeline construction.
    For example the `audiotestsrc` and the `audiomixer` both share a wide range of Audio-Formats, Sample-Rates and
    Bit-Depths that both can support. Linking them might produce a result, that works initially, but fails when the 
    RTP-Receiving-Bin is added later.
    
    To circumvent this, Caps are should specified at for links that can be made in multiple ways. This ensures reproducible
    results and avoids unexpected dynamic re-negotiation. 
