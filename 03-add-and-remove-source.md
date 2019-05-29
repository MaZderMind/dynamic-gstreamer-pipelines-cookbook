# Adding and Removing Sources
- [Sourcecode](03-add-and-remove-source.py)

This example is based upon [01-add-source.py](01-add-source.py). A Pipeline with a live `audiotestsrc`, an `audiomixer`
and an `autoaudiosink` is created. After 2 seconds, a second `audiotestsrc` is created, added to the pipeline and linked
to the Mixer. Another 2 seconds later it is stopped, unlinked and removed again. The process repeats as long as the
experiment runs.

You should read [Adding a Source](01-add-source.md) before this, because important Aspects that have been explained there
are not repeated here.

The most important new Lines have been marked as such:

 1. Because the Sequencing is done in a background thread and the Sequence will run over and over again, we need a way
    to stop the Sequence when the Main-Program terminates. In Python it is best to use the `threading.Event` Class and its
    `wait`-Method to achieve this.

 2. We want to remove all Elements that are added. One way to do this is to keep references to the actual Elements, like
    we do in these global variables. A even better way would be to collect the added Elements in a `Bin`, a Cluster of
    Elements, which can be added and removed as a whole. See [Adding and Removing RTP-Sources](04-add-and-remove-network-source.py)
    for an Example of using a Bin.

 3. In [Adding a Source](01-add-source.py) we used `Element.link_filtered` to create a similar link between the 
    `audiotestsrc` and the `audiomixer`. `link_filtered` creates and adds `capsfilter`-Element for us behind the scenes
     and places it between the Test-Source and the Audiomixer. When we later try to remove the Test-Source, the 
     `capsfilter`-Element would not automatically removed for us and we would need to figure out a way to get hold of a
     reference to this Element.
     
     To avoid that, this Example explicitly created a `capsfilter` and links it, so we already have a Reference to it.
     Another Option, explored in the next Experiment [Adding and Removing RTP-Sources](04-add-and-remove-network-source.py)
     is to use a Bin. The automatically created `capsfilter`-Element would then be a Child of that Bin and removed when
     the Bin is removed.
     
     For the same reason a Sink-Pad on the Mixer is requested explicitly. Usually a call to `Element.link` targeting
     an Element with request-Pads will automatically request a Pad for you, but then you need to figure out a way to
     explicitly select this pad later, when you intend to release the requested Mixer-Pad.

 4. Debugging these Scenarios can be quite complex. `Gst.debug_bin_to_dot_file_with_ts` is a Utility-Method which
    generates a [GraphViz](https://www.graphviz.org/)-File in the directory named in the Environment-Variable 
    `GST_DEBUG_DUMP_DOT_DIR`. To generate such files, you can run the Experiment like this:
    ```
    GST_DEBUG_DUMP_DOT_DIR=. ./04-add-and-remove-network-source.py
    ```
    
    To view theses Files, which can become rather large, I suggest [xdot](https://github.com/jrfonseca/xdot.py) which
    can be used on all major OSes and is really handy to view and examine these large dot-File graphs.

 5. Actually removing a Source is rather straight forward. First the State of all involved Elements is set to `NULL`,
    starting with the Source and moving down the Buffer-Flow. This will release any Resources held by the Elements and
    ensures that the Sources does not try to push new Buffers into an Element that has already been stopped.
    
    Next the Elements are removed from the Pipeline in the same order. This will also remove the Links between them.
    
    Lastly the Sink-Pad will be released to the Mixer.
