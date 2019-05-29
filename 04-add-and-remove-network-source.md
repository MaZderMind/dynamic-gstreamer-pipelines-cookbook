## Adding and Removing RTP-Sources
As a more realistic example of adding and removing Sources to a playing Pipeline, this Example creates a Pipeline with an
`audiotestsrc` and an `audiomixer`. After a while, a Bin (a Cluster of Elements) which receives and decodes Audio coming
from the Network via RTP is created, added to the Pipeline and linked to the `audiomixer`. After 4 and 6 seconds additional
Bins of this kind are created and also linked. Then, again with 2 Seconds in between, the Source-Bins are removes again,
before thw whole process starts over again.

Network-Sources can, for example. look like the following Pipeline. If you want, you can start such Pipelines on different
Computers across the Network, just adjust the destination IP-Address. 
```
gst-launch-1.0 audiotestsrc freq=220 is-live=true ! \
  audio/x-raw,format=S16BE,rate=48000,channels=2 ! \
  rtpL16pay ! \
  application/x-rtp,clock-rate=48000,media=audio,encoding-name=L16,channels=2 ! \
  udpsink host=127.0.0.1 port=10000
```

You should read [Adding RTP Network-Sources](02-add-network-source.md) and [Adding and Removing Sources](03-add-and-remove-source.md)
before this, because important Aspects that have been explained there are not repeated here.

The most important new Lines have been marked as such:

 1. In this Example we create a Bin to collect all the Elements that comprise the RTP-Source and manage them together.
    This also helps avoid some of the Problems described in [Adding and Removing Sources](03-add-and-remove-source.md).
    We also give the bin a unique name, so that it can be found by name again later. We could also store the Reference
    to the bin, depending on the use-case. 

 2. We selecl the Src-Pad of the last Element in the Bin and explicitly create a Ghost-Pad for it. This pad is added as
    Src-Pad to the Bin.  

 3. Because the Bin now has an unlinked Src-Pad, we can just use `Element.link` to link it to the Audio-Mixer.
 
 4. Upon removing we select the Bin's src-Pad by its name and thr select the Pad's Peer - which we know is the Mixer-Pad.
    This reference is kept for releasing the Mixer-Pad later.
 
 5. Before removing the Bin we set its State to `NULL`. This propagates the State-Change to its Children in the correct
    order. Then the Bin is removed, which removes all of its Children, too. Finally the requested Mixer-Pad is released. 
