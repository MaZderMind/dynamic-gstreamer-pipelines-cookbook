# GStreamer Dynamic Pipelines Cookbook

Writing complex, static GStreamer Pipelines, that is Pipelines that are fully described before launching them, is easy. 
Ok, not trivially easy but comparably easy. One has to only work with a single State that either works or doesnt 
(because of various reasons that themselves are sometimes not so easy).

Actually there are no static Pipelines - Depending on changing Input, Output or Properties Pipelines can re-negotiate 
Caps, Latency and other properties, but we can make our Pipelines quite static and well-known by placing CapsFilter 
between the Elements to enforce the Caps that we know beforehand and undermine any dynamic negotiation this way.
Most of this is done for us and happens behind the scene.

But things get quite a lot more complex when we want to change the Pipelines while they are running, without 
interrupting other pieces of the Pipeline. Now *we* need to take control of the State of both, our new and our existing 
Pipeline-Pieces and *we* need to mange their Startup-Behaviour, Latency and Running-Times.

Similar when we want to remove a Piece of our Pipeline, we need to correctly shutting down the individual Pieces and 
manage their links.

Dynamic Pipelines are a Thing I tried to ignore for as long as possible, but with this Blog-Post I want to give 
reproducible Examples for the most common Modifications: Adding and Removing Sinks and Sources and changing Links between
existing Elements.

## Running the Experiments
The Experiments require a little Test-Bed to run in, which includes a nice colorful console logger that helps a lot to
find orientation in the rather long and repetitive log outputs.

To run the Experiments create a virtualenv and install the dependencies in there:
```
virtualenv -ppython3 env
source ./env/bin/activate
./env/bin/pip install -r requirements.txt

./01-add-source.py
```

## Adding a Source
This Example creates a Pipeline with an `audiotestsrc` and an `audiomixer`. After a while a second `audiotestsrc` is
created, added to the Pipeline and linked to the `audiomixer`.

 - [Recipe](01-add-source.md)
 - [Sourcecode](01-add-source.py)

## Adding RTP-Sources
As a more realistic example of adding Sources to a playing Pipeline, this Example creates a Pipeline with an
`audiotestsrc` and an `audiomixer`. After a while, a Bin (a Cluster of Elements) which receives and decodes Audio coming
from the Network via RTP is created, added to the Pipeline and linked to the `audiomixer`. After 4 and 6 seconds additional
Bins of this kind are created and also linked.

 - [Recipe](02-add-network-source.md)
 - [Sourcecode](02-add-network-source.py)

## Adding and Removing Sources
This example is based upon [Adding a Source](01-add-source.py). A Pipeline with a live `audiotestsrc`, an `audiomixer`
and an `autoaudiosink` is created. After 2 seconds, a second `audiotestsrc` is created, added to the pipeline and linked
to the Mixer. Another 2 seconds later it is stopped, unlinked and removed again. The process repeats as long as the
experiment runs.

You should read [Adding a Source](01-add-source.md) before this, because important Lines that have been explained there
are not repeated here.

 - [Recipe](03-add-and-remove-source.md)
 - [Sourcecode](03-add-and-remove-source.py)

## Adding and Removing RTP-Sources
As a more realistic example of adding and removing Sources to a playing Pipeline, this Example creates a Pipeline with an
`audiotestsrc` and an `audiomixer`. After a while, a Bin (a Cluster of Elements) which receives and decodes Audio coming
from the Network via RTP is created, added to the Pipeline and linked to the `audiomixer`. After 4 and 6 seconds additional
Bins of this kind are created and also linked. Then, again with 2 Seconds in between, the Source-Bins are removes again,
before thw whole process starts over again.

You should read [Adding RTP-Sources](02-add-network-source.md) and [Adding and Removing Sources](03-add-and-remove-source.md)
before this, because important Aspects that have been explained there are not repeated here.

 - [Recipe](04-add-and-remove-network-source.md)
 - [Sourcecode](04-add-and-remove-network-source.py)

## Help, my $Thing does not work
Lalafoo Mailinglist
