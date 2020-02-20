## TUTORIAL 002 - Basic rhythm and sequencing

This tutorial introduces some methods for sequencing your sounds 
into rhythms and otherwise scheduling events in nonrealtime with pippi.

As usual, lets import the `dsp` module from pippi first.



```python
from pippi import dsp
```



### The Dub Pattern

Essentially all forms of sequencing in pippi are ultimately just copying the 
values from one section of one buffer onto the values from another section of 
a different buffer. This can happen at all sorts of levels and a useful pattern 
for doing it is basically just a bit of normal python.

We'll get some more into synthesis in future tutorials, but for fun lets demonstrate 
the dub pattern by synthesizing some percussion-ish sounds with the `noise` module.

This module has basic band-limited noise generation available with `noise.bln()` which 
will choose a new random frequency within a range you specify on every period of a simple 
wavetable synth. So you can generate a sinewave that jumps discretely around a boundry
within for example 1,000 to 2,000 hz. Those boundries can be curves to create filter-sweep-like 
shapes over time.

Lets make a little hi hat type sound by synthesizing 80ms of sine noise sweeping from between 9,000 and 12,000 hz 
to between 11,000 and 14,000 hz over the shape of the right half of a hanning window.

That maybe sounds like a lot but we'll do it pretty simply bit by bit. First, the curves!

The lower end of the hi hat will go from 9khz to 11khz:


```python
lowhz = dsp.win('hannin', 9000, 11000)

# Graph it
lowhz.graph('docs/tutorials/figures/002-lowhz-hann-curve.png')
```



<img src="/docs/tutorials/figures/002-lowhz-hann-curve.png" title="lowhz hann curve"/>

The upper end of the hi hat will go from 12khz to 14khz over the same shape pictured above.


```python
highhz = dsp.win('hannin', 12000, 14000)
```



Now lets make 80ms of noise with the curves:


```python
from pippi import noise 

hat = noise.bln('sine', dsp.MS*80, lowhz, highhz)
```



Lets give it an envelope with a sharp attack as well. The `pluckout` built-in wavetable 
looks like this:


```python
pluckout = dsp.win('pluckout')
pluckout.graph('docs/tutorials/figures/002-pluckout.png')
```



<img src="/docs/tutorials/figures/002-pluckout.png" title="pluckout wavetable"/>


```python
hat = hat.env(pluckout) * 0.5 # Finally multiply by half to reduce the amplitude of the signal
hat.write('docs/tutorials/renders/002-plucked-hat.ogg')
```



<audio src="/docs/tutorials/renders/002-plucked-hat.ogg" controls></audio>

We'll wrap it in a function to make it easy to reuse later on. Lets also change the 
curve shape of the frequency boundries to a different shape each time the function is 
called and a single hat sound is rendered, to give it a little bit of a shimmery imperfect 
sound. We'll also accept a length param to be able to vary the length of the hat.


```python

def makehat(length=dsp.MS*80):
    lowhz = dsp.win('rnd', 9000, 11000)
    highhz = dsp.win('rnd', 12000, 14000)
    return noise.bln('sine', length, lowhz, highhz).env(pluckout) * 0.5
```



Ok, now that we can make a hi hat sound on demand, lets try sequencing a series of 
hi hat hits in a row, evenly spaced at half-second intervals, and vary the length of the 
hat randomly from 100ms to 1s as we go.

Remember our output buffer `out`? For this simple but very useful form of the dub pattern, 
we'll keep track of our position inside the buffer as we go, and dub our hat sounds into 
it as we go.

Now we can loop until we get to the end of the 30 second buffer, advancing the time in our `elapsed` 
variable by a half second to sequence it in time.

Instead of just randomly picking a length for our hats, lets have them sample a point in a curve as 
they go to demonstrate a very easy way to create LFO controls.


```python

lfo = dsp.win('sinc', 0.1, 1) # Hat lengths between 100ms and 1s over a sinc window
lfo.graph('docs/tutorials/figures/002-sinc-win.png', label='sinc window')

out = dsp.buffer(length=30)

elapsed = 0
while elapsed < 30: 
    pos = elapsed / 30 # position in the buffer between 0 and 1
    hatlength = lfo.interp(pos) # Sample the current interpolated position in the curve to get the hat length
    hat = makehat(hatlength)
    out.dub(hat, elapsed) # Finally, we dub the hat into the output buffer at the current time
    elapsed += 0.5 # and move our position forward again a half second so we can do it all again!

out.write('docs/tutorials/renders/002-hats-on-ice.ogg')
```



<img src="/docs/tutorials/figures/002-sinc-win.png" title="sinc wavetable"/>

Behold! Our fabulous hi hats:

<audio src="/docs/tutorials/renders/002-hats-on-ice.ogg" controls></audio>

Pretty boring but it can keep a steady beat! Before we introduce some other sequencing tools, I want to
point out that this pattern might seem obvious and simplistic, but it's a very powerful way to design a 
custom algorithm for moving back and forth in time during your render process. You can add or subtract from 
`elapsed` to control the direction, leap from one point in time to another based on for example the pitch of 
the current note... for a simple example instead of using a fixed 0.5 second accumulator, lets create a new lfo 
and modulate the amount of time that elapses on each render iteration.


```python
from pippi import fx # The hats sound nice with a butterworth lowpass

length_lfo = dsp.win('sinc', 0.1, 1) 
time_lfo = dsp.win('hann', 0.001, 0.2) # Time increments between 1ms and 200ms over a sinc curve
time_lfo.graph('docs/tutorials/figures/002-time-lfo.png', label='time lfo')

out = dsp.buffer(length=30) # Otherwise we'll keep adding to our last buffer

elapsed = 0 # reset the clock
while elapsed < 30:
    # Our relative position in the buffer from 0 to 1
    pos = elapsed / 30

    # The length of the hat sound, sampled from the value of a sinc curve
    # at the current position in the output buffer
    hatlength = length_lfo.interp(pos) 

    # Call out hi hat function which returns a SoundBuffer
    hat = makehat(hatlength)

    # Dub the hi hat sound into our output buffer at the current position in seconds
    out.dub(hat, elapsed) 

    # Sample a length from the time_lfo at this position to determine how far ahead to 
    # move before the loop comes back around to dub another hat.
    beat = time_lfo.interp(pos)
    elapsed += beat

# Add a butterworth lowpass with a 3k cutoff
out = fx.lpf(out, 3000)
out.write('docs/tutorials/renders/002-hats-slipping-on-ice.ogg')
```



Here's our time LFO:

<img src="/docs/tutorials/figures/002-time-lfo.png" title="time lfo"/>

And our irregular sequence of hi hats:

<audio src="/docs/tutorials/renders/002-hats-slipping-on-ice.ogg" controls></audio>

