# GStreamer Dynamic Pipelines Cookbook

Writing complex, static GStreamer Pipelines, that is Pipelines that are fully described before launcing them, is easy. 
Ok, not trivially easy but comparably easy. One has to only work with a single State that either works or doesnt 
(because of various reasons that themselves are sometimes not so easy).

Actually there are no static Piplines - Depending on changing Input, Output or Properties Pipelines can re-negotiate 
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

## Adding a Source
This Example creates a Pipeline with an `audiotestsrc` and an `audiomixer`. After a while a second `audiotestsrc` is
created, added to the Pipeline and linked to the `audiomixer`.

 - [Recipe](01-add-source.md)
 - [Sourcecode](01-add-source.py)

## Adding an RTP-Source
As a more realistic example of adding Sources to a playing Pipeline, this Example creates a Pipeline with an
`audiotestsrc` and an `audiomixer`. After a while, a Bin (a Cluster of Elements) which receive and decode Audio coming
from the Network via RTP is created, added to the Pipeline and linked to the `audiomixer`. After 4 and 6 seconds additional
Bins of this kind are created and also linked.

 - [Recipe](02-add-network-source.md)
 - [Sourcecode](02-add-network-source.py)
