using System;
using System.IO;
using System.Text;

class BeatGenerator
{
    const int SR = 44100;

    public static void Generate(string path, double duration)
    {
        int n = (int)(duration * SR);
        float[] left = new float[n];
        float[] right = new float[n];

        double bpm = 90.0;
        double beat = 60.0 / bpm;
        double bar = beat * 4.0;
        int bars = (int)Math.Ceiling(duration / bar);

        int[][] chords = new int[][]
        {
            new int[] { 57, 60, 64, 67 }, // Am7
            new int[] { 53, 57, 60, 64 }, // Fmaj7
            new int[] { 48, 52, 55, 59 }, // Cmaj7
            new int[] { 55, 59, 62, 67 }  // G6
        };

        Random rnd = new Random(20261022);

        for (int b = 0; b < bars; b++)
        {
            double t0 = b * bar;
            int[] ch = chords[b % 4];

            AddBass(left, right, t0, beat * 1.7, MidiToFreq(ch[0] - 12), 0.30);
            AddBass(left, right, t0 + 2.0 * beat, beat * 1.3, MidiToFreq(ch[0] - 12), 0.22);

            AddKick(left, right, t0, 0.80, rnd);
            AddKick(left, right, t0 + 2.0 * beat, 0.68, rnd);
            if (b % 2 == 1) AddKick(left, right, t0 + 2.75 * beat, 0.45, rnd);

            AddSnare(left, right, t0 + beat, 0.30, rnd);
            AddSnare(left, right, t0 + 3.0 * beat, 0.36, rnd);

            for (int i = 0; i < 8; i++)
            {
                double amp = (i % 2 == 0) ? 0.085 : 0.050;
                AddHat(left, right, t0 + i * beat / 2.0, amp, rnd);
            }

            AddChord(left, right, t0, bar * 0.95, ch, 0.055);

            for (int i = 0; i < 4; i++)
            {
                int note = ch[(i + 1) % ch.Length] + 12;
                AddPluck(left, right, t0 + i * beat * 0.75, MidiToFreq(note), 0.045);
            }
        }

        AddRain(left, right, 9.0, Math.Max(0.0, duration - 9.0), 0.055, rnd);
        AddCrackle(left, right, 0.0, duration, 0.018, rnd);

        float max = 0.0f;
        for (int i = 0; i < n; i++)
        {
            float a = Math.Abs(left[i]);
            float b = Math.Abs(right[i]);
            if (a > max) max = a;
            if (b > max) max = b;
        }
        float gain = max > 0.0001f ? 0.72f / max : 1.0f;
        for (int i = 0; i < n; i++)
        {
            left[i] *= gain;
            right[i] *= gain;
        }

        WriteWav(path, left, right);
    }

    static double MidiToFreq(int midi)
    {
        return 440.0 * Math.Pow(2.0, (midi - 69) / 12.0);
    }

    static void AddTo(float[] l, float[] r, int index, double value, double pan)
    {
        if (index < 0 || index >= l.Length) return;
        double pl = Math.Sqrt((1.0 - pan) * 0.5);
        double pr = Math.Sqrt((1.0 + pan) * 0.5);
        l[index] += (float)(value * pl);
        r[index] += (float)(value * pr);
    }

    static void AddKick(float[] l, float[] r, double start, double amp, Random rnd)
    {
        int s0 = (int)(start * SR);
        int len = (int)(0.42 * SR);
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double f = 115.0 * Math.Exp(-t * 18.0) + 42.0;
            double env = Math.Exp(-t * 8.0);
            double click = (i < 120) ? (rnd.NextDouble() * 2.0 - 1.0) * 0.15 * (1.0 - i / 120.0) : 0.0;
            double v = Math.Sin(2.0 * Math.PI * f * t) * env * amp + click * amp;
            AddTo(l, r, s0 + i, v, 0.0);
        }
    }

    static void AddSnare(float[] l, float[] r, double start, double amp, Random rnd)
    {
        int s0 = (int)(start * SR);
        int len = (int)(0.22 * SR);
        double prev = 0.0;
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double noise = rnd.NextDouble() * 2.0 - 1.0;
            double hp = noise - prev;
            prev = noise;
            double env = Math.Exp(-t * 22.0);
            double tone = Math.Sin(2.0 * Math.PI * 180.0 * t) * Math.Exp(-t * 28.0) * 0.5;
            double v = (hp * 0.7 + tone) * env * amp;
            AddTo(l, r, s0 + i, v, (rnd.NextDouble() - 0.5) * 0.2);
        }
    }

    static void AddHat(float[] l, float[] r, double start, double amp, Random rnd)
    {
        int s0 = (int)(start * SR);
        int len = (int)(0.07 * SR);
        double prev = 0.0;
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double noise = rnd.NextDouble() * 2.0 - 1.0;
            double hp = noise - prev * 0.85;
            prev = noise;
            double env = Math.Exp(-t * 75.0);
            AddTo(l, r, s0 + i, hp * env * amp, 0.22);
        }
    }

    static void AddBass(float[] l, float[] r, double start, double dur, double freq, double amp)
    {
        int s0 = (int)(start * SR);
        int len = (int)(dur * SR);
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double env = Math.Exp(-t * 2.8) * (1.0 - Math.Exp(-t * 40.0));
            double v = Math.Sin(2.0 * Math.PI * freq * t) * 0.75
                     + Math.Sin(2.0 * Math.PI * freq * 2.0 * t) * 0.15;
            AddTo(l, r, s0 + i, v * env * amp, 0.0);
        }
    }

    static void AddChord(float[] l, float[] r, double start, double dur, int[] notes, double amp)
    {
        int s0 = (int)(start * SR);
        int len = (int)(dur * SR);
        for (int n = 0; n < notes.Length; n++)
        {
            double freq = MidiToFreq(notes[n]);
            double pan = -0.55 + 1.1 * n / Math.Max(1, notes.Length - 1);
            for (int i = 0; i < len; i++)
            {
                double t = i / (double)SR;
                double attack = 1.0 - Math.Exp(-t * 8.0);
                double release = Math.Exp(-t * 0.55);
                double env = attack * release;
                double v = Math.Sin(2.0 * Math.PI * freq * t) * 0.75
                         + Math.Sin(2.0 * Math.PI * freq * 2.0 * t) * 0.12
                         + Math.Sin(2.0 * Math.PI * freq * 3.0 * t) * 0.05;
                AddTo(l, r, s0 + i, v * env * amp, pan);
            }
        }
    }

    static void AddPluck(float[] l, float[] r, double start, double freq, double amp)
    {
        int s0 = (int)(start * SR);
        int len = (int)(0.30 * SR);
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double env = Math.Exp(-t * 10.0) * (1.0 - Math.Exp(-t * 120.0));
            double v = Math.Sin(2.0 * Math.PI * freq * t) * env * amp;
            AddTo(l, r, s0 + i, v, 0.12);
        }
    }

    static void AddRain(float[] l, float[] r, double start, double dur, double amp, Random rnd)
    {
        int s0 = (int)(start * SR);
        int len = (int)(dur * SR);
        double lpL = 0.0, lpR = 0.0;
        for (int i = 0; i < len; i++)
        {
            double t = i / (double)SR;
            double nL = rnd.NextDouble() * 2.0 - 1.0;
            double nR = rnd.NextDouble() * 2.0 - 1.0;
            lpL = lpL * 0.965 + nL * 0.035;
            lpR = lpR * 0.965 + nR * 0.035;
            double fade = Math.Min(1.0, t / 1.5) * Math.Min(1.0, (dur - t) / 1.5);
            double mod = 0.75 + 0.25 * Math.Sin(2.0 * Math.PI * 0.13 * t);
            AddTo(l, r, s0 + i, lpL * amp * fade * mod, -0.8);
            AddTo(l, r, s0 + i, lpR * amp * fade * mod, 0.8);
        }
    }

    static void AddCrackle(float[] l, float[] r, double start, double dur, double amp, Random rnd)
    {
        int s0 = (int)(start * SR);
        int len = (int)(dur * SR);
        int count = (int)(dur * 9.0);
        for (int k = 0; k < count; k++)
        {
            int pos = s0 + rnd.Next(len);
            double v = (rnd.NextDouble() * 2.0 - 1.0) * amp;
            double pan = rnd.NextDouble() * 2.0 - 1.0;
            AddTo(l, r, pos, v, pan);
        }
    }

    static void WriteWav(string path, float[] l, float[] r)
    {
        int n = Math.Min(l.Length, r.Length);
        int dataSize = n * 2 * 2;
        using (FileStream fs = new FileStream(path, FileMode.Create, FileAccess.Write))
        using (BinaryWriter bw = new BinaryWriter(fs))
        {
            bw.Write(Encoding.ASCII.GetBytes("RIFF"));
            bw.Write(36 + dataSize);
            bw.Write(Encoding.ASCII.GetBytes("WAVE"));
            bw.Write(Encoding.ASCII.GetBytes("fmt "));
            bw.Write(16);
            bw.Write((short)1);
            bw.Write((short)2);
            bw.Write(SR);
            bw.Write(SR * 2 * 2);
            bw.Write((short)(2 * 2));
            bw.Write((short)16);
            bw.Write(Encoding.ASCII.GetBytes("data"));
            bw.Write(dataSize);
            for (int i = 0; i < n; i++)
            {
                short sl = (short)(Math.Max(-1.0f, Math.Min(1.0f, l[i])) * 32767.0f);
                short sr = (short)(Math.Max(-1.0f, Math.Min(1.0f, r[i])) * 32767.0f);
                bw.Write(sl);
                bw.Write(sr);
            }
        }
    }
}
