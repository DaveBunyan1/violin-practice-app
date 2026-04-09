# Autocorrelation for pitch detection

## Overview

Autocorrelation measures how similar a signal is to a delayed (lagged) version of itself. It is commonly used to detect repeating patterns or periodic structure in a time series.

---

## Intuition

Sound is a vibration in air, and musical notes correspond to periodic waveforms — signals that repeat over time.

The frequency of a sound tells us how many times the waveform repeats per second, measured in Hertz (Hz). This frequency determines the pitch we hear:

- Higher frequency → higher pitch (e.g. E5)
- Lower frequency → lower pitch (e.g. G3)

For example:

A4 = 440 Hz → waveform repeats 440 times per second
A5 = 880 Hz → waveform repeats twice as fast

Even though real instruments like the violin produce complex sounds (not perfect sine waves), their signals are still periodic, meaning:

$$
𝑥(𝑡) \approx 𝑥(𝑡 + 𝑇)
$$

where $𝑇$ is the period of the waveform.

---

#### Key Idea

If we take a short segment of audio and shift it slightly, then compare it to the original:

- If the shift is random → the signals don’t match
- If the shift equals the period → the waveform aligns with itself and similarity is maximized

This alignment is exactly what autocorrelation measures.

---

#### Why this matters for pitch detection

Since each musical note has a characteristic frequency (and therefore a characteristic period):

- The waveform repeats at regular intervals
- Autocorrelation will produce a peak at the lag corresponding to that period

At the correct lag (equal to the period), peaks and troughs of the waveform line up, producing a strong peak in the autocorrelation function.

By finding this lag, we can recover:

- the period $𝑇$ (one cycle takes $T$ seconds)
- and therefore the frequency $𝑓 = 1 / 𝑇$

If the lag is measured in samples (denoted by $\tau$), we convert it to time using the sample rate $f_s$:

$$
T = \frac{\tau}{f_s}
\quad \Rightarrow \quad
f = \frac{f_s}{\tau}
$$

Example:
Let $T = 0.002$ seconds, meaning the waveform repeats every $0.002$ seconds.
The number of repetitions per second is:

$$
\frac{1}{0.002} = 500
$$

So the frequency is:
$f = 500 \text{ Hz}$.

In practice, we work with discrete samples rather than continuous time. Autocorrelation is computed over sample lags, and the period is estimated as the lag (in samples) where the first significant peak occurs.

---

#### Mathematical Definition

The autocorrelation function is defined as:

$$
R(\tau) = \sum_{t=0}^{N-1} x(t)\,x(t + \tau)
$$
