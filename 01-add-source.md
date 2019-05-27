# Adding a Source
→ [Sourcecode](01-add-source.py)

This Example creates a Pipeline like this:

```
  audiotestsrc is-live=true ! audiomixer ! autoaudiosink
```

It installs Pad-Probes after the audiotestsrc and the audiomixer, which log the PTS-Timestamps of the Buffers flowing 
through the Element's src-Pads.

After 2 seconds, another audiotestsrc is created with such a Pad-Probe and linked to the audiomixer.

On the Speaker/Headphone you can hear the 220 Hz-Zone from the first audiotestsrc, which after 2 Seconds gets mixed with
the 440 Hz Tone from the second audiotestsrc.

On the Console you can see that the Timestamps from the second audiotestsrc start around the 0:00:02 seconds mark, 
because we configured it to be a true live-source.

The most important Lines have been marked as such:

 1. We schedule the execution on the GLib Event-Loop by using `Glib.idle_add`. On the Console you can see, that the
    Sequence runs in its own `Sequence`-Thread but the second Test-Source is actually added from the `MainThread`.

    It seems that this exact example also works without this, because some of the Methods are Thread-Safe by
    Documentation (ie. [Bin.add](https://lazka.github.io/pgi-docs/#Gst-1.0/classes/Bin.html#Gst.Bin.add)) and some are
    by luck (ie [GObject.Object.set_property](https://lazka.github.io/pgi-docs/#GObject-2.0/classes/Object.html#GObject.Object.set_property)),
    but not following this pattern can lead to unexpected and hard to find issues.

    From the console you can also see, that the Pad-Probes are called synchronously from their respective Elements' 
    Streaming-Threads (Shown as `Dummy-[n]`).

 2. Forcing the `audiotestsrc` to be a Live-Source makes it produce Buffers with timestamps starting at the current
    Running-Time of the Pipeline. A Non-Live-Source would start ad 0:00:00 and run faster then the other sources,
    until it would have caught up to the current Running-Time.

    Try to comment the Line marked with `(2)` out and look at the Console-Output around the 0:00:02 seconds mark

3. Furthermore it is important that all other Sources in the Pipeline are also in Live-Mode, here this is ensured
    by setting the `is-live` property of `testsrc1`. If one of the Sources connected to the same downstream Elements
    (here for example the `audsiomixer`) are not live, they will produce as many buffers as the sink allows them to. 
    In a pipeline like the following, where neither source nor sink enforces live-behaviour, the timestamp the 
    audiomixer is working with might be way ahead of those produced by your newly added live-source:
    `audiotestsrc ! audiomixer ! wavenc ! filesink …`
    
    But even if your sink is live, like an `alsasink` for example, the timestamp at the `audiomixer` might be multiple
    seconds ahead of your new Live-Source. GStreamer will then halt the downstream elements until you new Live-Source
    has caught up, possibly dropping data from other Live-Sources and not sending any Buffers out to the sink.

    If you are dealing with sources that do not support live behaviour, for example a `filesrc`, you should place an
    `identity`-Element with the `sync`-Property set to True right after it, so that it behaves like a live-source to
    downstream elements like `audiomixer`s.

 4. An Element does not automatically take over its parent state. Also, not all Elements in a Pipeline have to have the
    same state. In this case the new `audiotestsrc`-Element starts in `NULL` state and is added as such to the Pipeline.
    Once it is added, its state is synced to the pipeline (`PLAYING`) which makes it switch from `NULL` through
    `READY` and `PAUSED` to `PLAYING`, where it then starts generating buffers and sending them downstream to the 
    `audiomixer`.
