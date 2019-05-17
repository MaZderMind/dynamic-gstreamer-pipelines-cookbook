# GStreamer Dynamic Pipelines Cookbook

Writing complex, static GStreamer Pipelines, that is Pipelines that are fully described before launcing them, is easy. 
Ok, not trivially easy but comparably easy. One has to only work with a single State that either works or doesn't 
(because of various reasons that themselfs are sometimes not so easy).

Actually there are no static Piplines - Depending on changing Input, Output or Properties Pipelines can re-negotiate 
Caps, Latency and other properties, but we can make our Pipelines quite statatic and well-known by placing CapsFilter 
between the Elements to enforce the Caps that we know beforehand and undermine any dynamic negotiation this way.
Most of this is done for us and happens behind the scene.

But things get quite a lot more complex when we want to change the Pipelines while they are running, without 
interrupting other pieces of the Pipeline. Now *we* need to take control of the State of both, our new and our existing 
Pipeline-Pieces and *we* need to manger their Startup-Behaviour and Running-Times.

Similar when we want to remove a Piece of our Pipeline, we need to correctly shutting down the individual Pieces and 
manage their links.

Dynamic Pipelines are a Thing I tried to ignore for as long as possible, but with this Blog-Post I want to give 
reproducible Examples for the most 4 most common Modifications: Adding and Removing Sinks and Sources.

## Adding a Source
This Example creates a Pipeline with an `audiotestsrc` and an `audiomixer`. After a while a second `audiotestsrc` is
created, added to the Pipeline and linked to the Audiomixer.

 - [Recipe](01-add-source.md)
 - [Sourcecode](01-add-source.py)
