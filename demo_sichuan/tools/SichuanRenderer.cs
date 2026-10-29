using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Text;

class SichuanRenderer
{
    const int W = 1280;
    const int H = 720;
    const int FPS = 30;
    const double DURATION = 30.0;

    static string root;
    static string framesDir;
    static string audioDir;
    static string assetsDir;
    static string outputDir;
    static FontFamily uiFont;
    static FontFamily handFont;

    static void Main(string[] args)
    {
        root = args.Length > 0 ? args[0] : Directory.GetCurrentDirectory();
        framesDir = Path.Combine(root, "output", "frames");
        audioDir = Path.Combine(root, "audio");
        assetsDir = Path.Combine(root, "assets");
        outputDir = Path.Combine(root, "output");

        Directory.CreateDirectory(framesDir);
        Directory.CreateDirectory(audioDir);
        Directory.CreateDirectory(Path.Combine(assetsDir, "characters"));
        Directory.CreateDirectory(Path.Combine(assetsDir, "scenes"));
        Directory.CreateDirectory(Path.Combine(assetsDir, "props"));
        Directory.CreateDirectory(outputDir);

        uiFont = new FontFamily("Microsoft YaHei");
        try { handFont = new FontFamily("KaiTi"); }
        catch { handFont = uiFont; }

        int total = (int)(DURATION * FPS);
        Console.WriteLine("Rendering " + total + " frames...");
        for (int f = 0; f < total; f++)
        {
            double t = f / (double)FPS;
            using (Bitmap bmp = new Bitmap(W, H))
            using (Graphics g = Graphics.FromImage(bmp))
            {
                SetupGraphics(g);
                DrawFrame(g, t);
                string path = Path.Combine(framesDir, string.Format("frame_{0:0000}.jpg", f));
                SaveJpeg(bmp, path, 92L);
            }
            if (f % 90 == 0) Console.WriteLine("  frame " + f + "/" + total);
        }

        Console.WriteLine("Generating Sichuan beat...");
        SichuanBeatGenerator.Generate(Path.Combine(audioDir, "beat.wav"), DURATION);

        Console.WriteLine("Generating assets...");
        GenerateAssets();

        Console.WriteLine("DONE");
    }

    static void SetupGraphics(Graphics g)
    {
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.PixelOffsetMode = PixelOffsetMode.HighQuality;
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
    }

    static void DrawFrame(Graphics g, double t)
    {
        g.Clear(Color.Black);
        int shot = Math.Min(5, (int)(t / 5.0));
        double local = (t - shot * 5.0) / 5.0;
        if (local < 0) local = 0;
        if (local > 1) local = 1;

        using (Bitmap scene = new Bitmap(W, H))
        using (Graphics sg = Graphics.FromImage(scene))
        {
            SetupGraphics(sg);
            DrawShot(sg, shot, local, t);

            double zoom, panX, panY;
            GetCamera(shot, local, out zoom, out panX, out panY);
            RectangleF dest = new RectangleF(
                (float)(-(zoom - 1.0) * W / 2.0 + panX),
                (float)(-(zoom - 1.0) * H / 2.0 + panY),
                (float)(W * zoom),
                (float)(H * zoom));
            g.DrawImage(scene, dest);
        }

        DrawVignette(g);
        DrawGrain(g, t);
        DrawSubtitles(g, t);
    }

    static void GetCamera(int shot, double local, out double zoom, out double panX, out double panY)
    {
        zoom = 1.0;
        panX = 0.0;
        panY = 0.0;
        double e = Ease(local);
        switch (shot)
        {
            case 0: zoom = 1.00 + 0.07 * e; panY = 3.0 * e; break;
            case 1: zoom = 1.03 + 0.05 * e; panY = -5.0 * e; break;
            case 2: zoom = 1.03 + 0.05 * e; panX = -16.0 + 32.0 * e; panY = -3.0 * e; break;
            case 3: zoom = 1.02 + 0.06 * e; panY = -7.0 * e; break;
            case 4: zoom = 1.00 + 0.06 * e; panX = 10.0 * e; break;
            case 5: zoom = 1.01 + 0.04 * e; break;
        }
    }

    static void DrawShot(Graphics g, int shot, double local, double t)
    {
        switch (shot)
        {
            case 0: DrawTeahouseWide(g, local, t); break;
            case 1: DrawTeaClose(g, local, t); break;
            case 2: DrawFaceChange(g, local, t); break;
            case 3: DrawHotpot(g, local, t); break;
            case 4: DrawRainAlley(g, local, t); break;
            case 5: DrawEndCard(g, local, t); break;
        }
    }

    // ---------- Subtitles ----------

    static readonly string[] SubTexts = new string[]
    {
        "雨点敲青瓦，盖碗泡时光",
        "莫慌嘛，龙门阵慢慢摆",
        "脸一换，红堂堂，满堂彩",
        "火锅一滚，椒麻烫心肠",
        "巴适得板，日子有腔调",
        "一碗茶，慢慢摆"
    };

    static readonly double[] SubStart = new double[] { 0.8, 5.2, 10.2, 15.2, 20.2, 25.4 };
    static readonly double[] SubEnd = new double[] { 4.8, 9.8, 14.8, 19.8, 24.8, 29.2 };

    static void DrawSubtitles(Graphics g, double t)
    {
        for (int i = 0; i < SubTexts.Length; i++)
        {
            if (t < SubStart[i] || t > SubEnd[i]) continue;
            double a = FadeIn(t, SubStart[i], SubStart[i] + 0.18) * FadeOut(t, SubEnd[i] - 0.18, SubEnd[i]);
            if (a <= 0.01) continue;
            DrawSubtitle(g, SubTexts[i], a);
        }
    }

    static void DrawSubtitle(Graphics g, string text, double alpha)
    {
        using (Font f = new Font(uiFont, 28.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        {
            SizeF sz = g.MeasureString(text, f);
            float padX = 22.0f;
            float padY = 9.0f;
            float w = sz.Width + padX * 2.0f;
            float h = sz.Height + padY * 2.0f;
            float x = (W - w) / 2.0f;
            float y = H - 86.0f;
            RectangleF box = new RectangleF(x, y, w, h);
            using (SolidBrush bg = new SolidBrush(Color.FromArgb((int)(150.0 * alpha), 10, 8, 8)))
            {
                using (GraphicsPath p = RoundPath(box, 12.0f)) g.FillPath(bg, p);
            }
            using (SolidBrush b = new SolidBrush(Color.FromArgb((int)(255.0 * alpha), 255, 245, 226)))
            {
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString(text, f, b, box, sf);
                }
            }
        }
    }

    // ---------- S01: teahouse wide ----------

    static void DrawTeahouseWide(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(5, 16, 20), C(14, 35, 39), 90);

        // distant alley silhouettes
        using (SolidBrush far = new SolidBrush(C(8, 22, 26)))
        {
            g.FillRectangle(far, 0, 200, W, 300);
            for (int i = 0; i < 9; i++)
            {
                float bx = i * 155 - 40;
                float bh = 100 + (i * 53) % 130;
                g.FillRectangle(far, bx, 330 - bh, 130, bh + 60);
            }
        }

        // wet ground
        Grad(g, new RectangleF(0, 520, W, 200), C(10, 27, 30), C(3, 8, 10), 90);
        DrawReflections(g, t, 0);

        // roof
        using (SolidBrush roof = new SolidBrush(C(18, 16, 15)))
        {
            g.FillRectangle(roof, 0, 0, W, 96);
        }
        using (Pen tile = new Pen(A(C(120, 80, 55), 90), 2))
        {
            for (int i = 0; i < 26; i++)
            {
                float x = i * 53;
                g.DrawLine(tile, x, 0, x + 26, 92);
            }
        }
        using (SolidBrush eave = new SolidBrush(C(28, 20, 16)))
        {
            g.FillRectangle(eave, 0, 90, W, 18);
        }
        using (Pen drip = new Pen(A(C(160, 210, 220), 90), 1.5f))
        {
            for (int i = 0; i < 32; i++)
            {
                float x = 20 + i * 40;
                float y = 112 + (float)((Math.Sin(t * 2.0 + i) + 1.0) * 7.0);
                g.DrawLine(drip, x, 108, x, y + 10);
            }
        }

        // teahouse facade
        RectangleF shop = new RectangleF(600, 190, 560, 390);
        using (SolidBrush wall = new SolidBrush(C(34, 23, 18)))
        {
            FillRound(g, wall, shop, 6);
        }
        using (SolidBrush trim = new SolidBrush(C(18, 13, 11)))
        {
            g.FillRectangle(trim, shop.X - 8, shop.Y - 10, shop.Width + 16, 16);
            g.FillRectangle(trim, shop.X - 8, shop.Bottom - 8, shop.Width + 16, 14);
        }

        // warm windows with lattice
        DrawWarmWindow(g, new RectangleF(635, 245, 190, 160), t);
        DrawWarmWindow(g, new RectangleF(865, 245, 250, 160), t);

        // door
        RectangleF door = new RectangleF(650, 420, 160, 150);
        using (SolidBrush d = new SolidBrush(C(74, 42, 24)))
        {
            FillRound(g, d, door, 4);
        }
        using (Pen frame = new Pen(C(22, 14, 10), 5))
        {
            g.DrawRectangle(frame, door.X, door.Y, door.Width, door.Height);
            g.DrawLine(frame, door.X + door.Width / 2, door.Y, door.X + door.Width / 2, door.Bottom);
        }
        using (SolidBrush glow = new SolidBrush(A(C(255, 190, 105), 36)))
        {
            g.FillRectangle(glow, door.X + 8, door.Y + 8, door.Width - 16, door.Height - 16);
        }

        // sign board with tea leaf icon (no readable text)
        RectangleF sign = new RectangleF(880, 160, 230, 58);
        using (SolidBrush sb = new SolidBrush(C(82, 39, 26)))
        {
            FillRound(g, sb, sign, 6);
        }
        using (Pen gold = new Pen(C(215, 162, 74), 3))
        {
            g.DrawRectangle(gold, sign.X + 4, sign.Y + 4, sign.Width - 8, sign.Height - 8);
        }
        DrawTeaLeaf(g, 916, 189, 26, 0.0);
        using (Font f = new Font(handFont, 24.0f, FontStyle.Bold, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(C(240, 205, 135)))
        {
            g.DrawString("老茶馆", f, b, 956, 174);
        }

        // red lanterns
        DrawLantern(g, 548, 178, 0.95f, t);
        DrawLantern(g, 1178, 178, 0.95f, t);

        // bamboo chairs and table silhouettes
        using (Pen bamboo = new Pen(C(112, 77, 44), 5))
        {
            for (int i = 0; i < 3; i++)
            {
                float x = 165 + i * 90;
                g.DrawLine(bamboo, x, 560, x, 650);
                g.DrawLine(bamboo, x + 46, 560, x + 46, 650);
                g.DrawLine(bamboo, x - 4, 560, x + 50, 560);
                g.DrawLine(bamboo, x - 4, 600, x + 50, 600);
                g.DrawLine(bamboo, x, 650, x - 14, 670);
                g.DrawLine(bamboo, x + 46, 650, x + 60, 670);
            }
        }
        using (SolidBrush table = new SolidBrush(C(58, 36, 24)))
        {
            FillRound(g, table, new RectangleF(128, 610, 310, 24), 4);
            g.FillRectangle(table, 155, 634, 14, 56);
            g.FillRectangle(table, 398, 634, 14, 56);
        }

        // foreground gaiwan
        DrawGaiwan(g, 285, 570, 1.05f, t, false);

        // rain
        DrawRain(g, t, 130, new RectangleF(0, 0, W, H), 55);

        // small chapter mark
        DrawChapterMark(g, "01 / 雨夜茶馆", 70, 660);
    }

    static void DrawWarmWindow(Graphics g, RectangleF r, double t)
    {
        using (LinearGradientBrush b = new LinearGradientBrush(r, C(248, 184, 95), C(174, 91, 42), 90f))
        {
            g.FillRectangle(b, r);
        }
        using (Pen frame = new Pen(C(27, 17, 12), 7))
        {
            g.DrawRectangle(frame, r.X, r.Y, r.Width, r.Height);
            g.DrawLine(frame, r.X + r.Width / 2, r.Y, r.X + r.Width / 2, r.Bottom);
            g.DrawLine(frame, r.X, r.Y + r.Height / 2, r.Right, r.Y + r.Height / 2);
            for (int i = 1; i < 4; i++)
            {
                float y = r.Y + i * r.Height / 4;
                g.DrawLine(frame, r.X, y, r.Right, y);
            }
        }
        using (SolidBrush warm = new SolidBrush(A(C(255, 190, 105), 18)))
        {
            g.FillRectangle(warm, r.X - 18, r.Y - 18, r.Width + 36, r.Height + 36);
        }
    }

    static void DrawRain(Graphics g, double t, int count, RectangleF area, int alpha)
    {
        for (int i = 0; i < count; i++)
        {
            double seed = i * 12.9898;
            double sx = (seed * 43758.5453) % 1.0;
            double sy = ((seed + 7.13) * 24634.6345) % 1.0;
            float x = area.X + (float)(sx * area.Width);
            float y = area.Y + (float)(((sy + t * 0.28) % 1.0) * area.Height);
            float len = 10.0f + (float)((i * 7) % 26);
            int a = alpha + (i % 4) * 8;
            using (Pen p = new Pen(A(C(190, 225, 235), a), 1.1f))
            {
                g.DrawLine(p, x, y, x - 3.0f, y + len);
            }
        }
    }

    static void DrawLantern(Graphics g, float x, float y, float s, double t)
    {
        DrawRadialGlow(g, new RectangleF(x - 100 * s, y - 40 * s, 200 * s, 220 * s), C(235, 68, 48), 42);
        using (Pen cord = new Pen(C(30, 20, 14), 3))
        {
            g.DrawLine(cord, x, y - 52 * s, x, y - 14 * s);
        }
        using (SolidBrush body = new SolidBrush(C(201, 44, 36)))
        {
            g.FillEllipse(body, x - 34 * s, y - 12 * s, 68 * s, 82 * s);
        }
        using (Pen rib = new Pen(A(C(255, 178, 95), 80), 1.4f))
        {
            for (int i = -2; i <= 2; i++)
            {
                g.DrawArc(rib, x - 30 * s + i * 9 * s, y - 10 * s, 20 * s, 78 * s, -80, 160);
            }
        }
        using (SolidBrush cap = new SolidBrush(C(214, 164, 74)))
        {
            g.FillRectangle(cap, x - 20 * s, y - 18 * s, 40 * s, 8 * s);
            g.FillRectangle(cap, x - 18 * s, y + 66 * s, 36 * s, 7 * s);
        }
        using (Pen tassel = new Pen(C(226, 172, 74), 2))
        {
            float sway = (float)Math.Sin(t * 1.6 + x * 0.01) * 4.0f;
            g.DrawLine(tassel, x, y + 74 * s, x + sway, y + 112 * s);
            g.DrawLine(tassel, x - 5, y + 74 * s, x - 5 + sway, y + 104 * s);
            g.DrawLine(tassel, x + 5, y + 74 * s, x + 5 + sway, y + 104 * s);
        }
    }

    // ---------- S02: tea close ----------

    static void DrawTeaClose(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(42, 25, 17), C(10, 10, 9), 90);
        DrawBokeh(g, local, 16, C(244, 176, 92), 0.15);

        // rain window in background
        RectangleF win = new RectangleF(690, 48, 520, 420);
        using (SolidBrush frame = new SolidBrush(C(22, 15, 12)))
        {
            FillRound(g, frame, win, 6);
        }
        RectangleF glass = new RectangleF(712, 70, 476, 376);
        using (LinearGradientBrush b = new LinearGradientBrush(glass, C(22, 57, 70), C(54, 99, 113), 90f))
        {
            g.FillRectangle(b, glass);
        }
        Random rnd = new Random(2026);
        for (int i = 0; i < 36; i++)
        {
            float x = glass.X + (float)rnd.NextDouble() * glass.Width;
            float y = glass.Y + 120 + (float)rnd.NextDouble() * (glass.Height - 120);
            float r = 3 + (float)rnd.NextDouble() * 15;
            using (SolidBrush b = new SolidBrush(Color.FromArgb(25 + rnd.Next(45), 255, 206, 140)))
            {
                g.FillEllipse(b, x - r, y - r, r * 2, r * 2);
            }
        }
        using (Pen mullion = new Pen(C(28, 18, 12), 9))
        {
            g.DrawLine(mullion, glass.X + glass.Width / 2, glass.Y, glass.X + glass.Width / 2, glass.Bottom);
            g.DrawLine(mullion, glass.X, glass.Y + glass.Height * 0.55f, glass.Right, glass.Y + glass.Height * 0.55f);
        }
        DrawRain(g, t, 70, glass, 45);
        using (SolidBrush warm = new SolidBrush(A(C(255, 178, 92), 26)))
        {
            g.FillRectangle(warm, glass.X, glass.Y, glass.Width, glass.Height);
        }

        // table
        Grad(g, new RectangleF(0, 480, W, 240), C(86, 52, 30), C(26, 15, 10), 90);
        using (Pen edge = new Pen(A(C(255, 210, 150), 52), 2))
        {
            g.DrawLine(edge, 0, 480, W, 480);
        }
        using (Pen grain = new Pen(A(C(52, 31, 18), 80), 1.2f))
        {
            for (int i = 0; i < 12; i++)
            {
                float y = 500 + i * 17;
                g.DrawLine(grain, 0, y, W, y + (float)Math.Sin(i) * 4);
            }
        }

        // gaiwan
        DrawGaiwan(g, 520, 420, 2.15f, t, true);

        // hand lifting lid
        DrawTeaHand(g, 700, 292, 1.15f, local);

        // small side plate with peanuts
        using (SolidBrush plate = new SolidBrush(C(228, 212, 180)))
        {
            g.FillEllipse(plate, 900, 548, 210, 44);
        }
        for (int i = 0; i < 9; i++)
        {
            float px = 938 + (i % 3) * 48;
            float py = 552 + (i / 3) * 13;
            using (SolidBrush pb = new SolidBrush(C(190, 132, 72)))
            {
                g.FillEllipse(pb, px, py, 28, 15);
            }
            using (Pen pl = new Pen(A(C(110, 70, 38), 130), 1))
            {
                g.DrawLine(pl, px + 7, py + 6, px + 20, py + 6);
            }
        }

        DrawSteam(g, 500, 330, t, 4, 150);
        DrawWarmRim(g, 380, 250, 360, 300, 0.14);
        DrawChapterMark(g, "02 / 盖碗茶", 70, 660);
    }

    static void DrawGaiwan(Graphics g, float x, float y, float s, double t, bool open)
    {
        // saucer
        using (SolidBrush saucer = new SolidBrush(C(236, 222, 198)))
        {
            g.FillEllipse(saucer, x - 82 * s, y + 40 * s, 164 * s, 36 * s);
        }
        using (SolidBrush saucer2 = new SolidBrush(C(208, 190, 164)))
        {
            g.FillEllipse(saucer2, x - 62 * s, y + 48 * s, 124 * s, 18 * s);
        }

        // bowl
        using (GraphicsPath bowl = new GraphicsPath())
        {
            bowl.AddBezier(x - 54 * s, y - 32 * s, x - 60 * s, y + 18 * s, x - 42 * s, y + 46 * s, x, y + 46 * s);
            bowl.AddBezier(x, y + 46 * s, x + 42 * s, y + 46 * s, x + 60 * s, y + 18 * s, x + 54 * s, y - 32 * s);
            bowl.CloseFigure();
            using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(x - 58 * s, y - 34 * s, 116 * s, 84 * s), C(255, 250, 236), C(212, 196, 172), 0f))
            {
                g.FillPath(b, bowl);
            }
        }
        using (Pen rim = new Pen(C(205, 58, 45), 3.0f * s))
        {
            g.DrawArc(rim, x - 54 * s, y - 34 * s, 108 * s, 20 * s, 180, 180);
        }
        // tea
        using (SolidBrush tea = new SolidBrush(C(178, 98, 32)))
        {
            g.FillEllipse(tea, x - 50 * s, y - 26 * s, 100 * s, 18 * s);
        }
        using (Pen shine = new Pen(A(C(255, 222, 160), 130), 2))
        {
            g.DrawArc(shine, x - 34 * s, y - 25 * s, 60 * s, 10 * s, 190, 150);
        }

        // lid
        if (!open)
        {
            using (SolidBrush lid = new SolidBrush(C(246, 236, 214)))
            {
                g.FillEllipse(lid, x - 52 * s, y - 42 * s, 104 * s, 24 * s);
            }
            using (Pen lidrim = new Pen(C(196, 184, 160), 2))
            {
                g.DrawEllipse(lidrim, x - 52 * s, y - 42 * s, 104 * s, 24 * s);
            }
            using (SolidBrush knob = new SolidBrush(C(218, 202, 174)))
            {
                g.FillEllipse(knob, x - 10 * s, y - 52 * s, 20 * s, 12 * s);
            }
        }
        else
        {
            // lid held above, tilted toward the hand
            using (SolidBrush lid = new SolidBrush(C(246, 236, 214)))
            {
                g.FillEllipse(lid, x - 24 * s, y - 58 * s, 96 * s, 22 * s);
            }
            using (Pen lidrim = new Pen(C(196, 184, 160), 2))
            {
                g.DrawEllipse(lidrim, x - 24 * s, y - 58 * s, 96 * s, 22 * s);
            }
        }

        DrawSteam(g, x, y - 40 * s, t, 3, 100 * s);
    }

    static void DrawTeaHand(Graphics g, float x, float y, float s, double local)
    {
        // Forearm comes in from the lower right, under a dark red sleeve.
        using (Pen arm = new Pen(C(232, 188, 150), 32 * s))
        {
            arm.StartCap = LineCap.Round;
            arm.EndCap = LineCap.Round;
            g.DrawLine(arm, x + 235 * s, y + 175 * s, x + 32 * s, y + 22 * s);
        }
        using (Pen sleeve = new Pen(C(122, 36, 32), 58 * s))
        {
            sleeve.StartCap = LineCap.Round;
            sleeve.EndCap = LineCap.Round;
            g.DrawLine(sleeve, x + 250 * s, y + 190 * s, x + 145 * s, y + 102 * s);
        }
        using (Pen cuff = new Pen(C(198, 162, 94), 3 * s))
        {
            cuff.StartCap = LineCap.Round;
            cuff.EndCap = LineCap.Round;
            g.DrawLine(cuff, x + 133 * s, y + 92 * s, x + 158 * s, y + 112 * s);
        }
        using (SolidBrush skin = new SolidBrush(C(238, 198, 163)))
        {
            g.FillEllipse(skin, x - 18 * s, y - 10 * s, 86 * s, 50 * s);
            g.FillEllipse(skin, x - 2 * s, y - 28 * s, 23 * s, 38 * s);
            g.FillEllipse(skin, x + 21 * s, y - 30 * s, 23 * s, 38 * s);
            g.FillEllipse(skin, x + 44 * s, y - 24 * s, 21 * s, 34 * s);
        }
        using (Pen line = new Pen(A(C(170, 110, 82), 100), 1.5f))
        {
            g.DrawArc(line, x + 10 * s, y + 4 * s, 24 * s, 20 * s, 20, 120);
            g.DrawArc(line, x + 36 * s, y + 2 * s, 24 * s, 20 * s, 20, 120);
        }
    }

    // ---------- S03: face change ----------

    static void DrawFaceChange(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(55, 13, 16), C(12, 8, 9), 90);

        // red curtain
        using (SolidBrush curtain = new SolidBrush(C(118, 24, 28)))
        {
            g.FillRectangle(curtain, 0, 0, W, 520);
        }
        using (Pen fold = new Pen(A(C(64, 10, 14), 110), 4))
        {
            for (int i = 0; i < 18; i++)
            {
                float x = i * 78 - 20;
                g.DrawLine(fold, x, 0, x + 28, 520);
            }
        }
        using (SolidBrush floor = new SolidBrush(C(42, 24, 18)))
        {
            g.FillRectangle(floor, 0, 500, W, 220);
        }
        using (Pen plank = new Pen(A(C(20, 10, 8), 130), 2))
        {
            for (int i = 0; i < 9; i++)
            {
                float y = 510 + i * 24;
                g.DrawLine(plank, 0, y, W, y);
            }
        }

        // stage spotlights
        DrawRadialGlow(g, new RectangleF(360, -40, 560, 620), C(255, 202, 120), 34);
        DrawRadialGlow(g, new RectangleF(80, 80, 300, 440), C(220, 60, 50), 20);

        // gong
        DrawGong(g, 150, 330, 1.0f, t);

        // audience silhouettes
        using (SolidBrush aud = new SolidBrush(C(8, 7, 7)))
        {
            for (int i = 0; i < 7; i++)
            {
                float x = 80 + i * 170;
                float y = 620 + (i % 2) * 12;
                g.FillEllipse(aud, x, y, 64, 64);
                FillRound(g, aud, new RectangleF(x - 10, y + 44, 84, 120), 28);
            }
        }

        // Xiao He
        double pose = Math.Sin(local * Math.PI * 2.0) * 0.5 + 0.5;
        DrawXiaoHe(g, 650, 560, 2.0f, local, pose);

        // floating masks
        DrawOperaMask(g, 960, 240, 1.15f, C(208, 45, 38), local + 0.1);
        DrawOperaMask(g, 1100, 360, 0.9f, C(24, 22, 24), local + 0.4);
        DrawOperaMask(g, 900, 400, 0.8f, C(212, 160, 64), local + 0.7);

        // gold dust
        Random rnd = new Random(303);
        for (int i = 0; i < 40; i++)
        {
            float x = rnd.Next(280, 1100);
            float y = 80 + (float)((rnd.NextDouble() * 400 + t * 18) % 400);
            using (SolidBrush b = new SolidBrush(Color.FromArgb(60 + rnd.Next(80), 238, 190, 100)))
            {
                g.FillEllipse(b, x, y, 3, 3);
            }
        }

        DrawChapterMark(g, "03 / 变脸", 70, 660);
    }

    static void DrawGong(Graphics g, float x, float y, float s, double t)
    {
        using (Pen stand = new Pen(C(38, 24, 18), 6))
        {
            g.DrawLine(stand, x - 70 * s, y + 120 * s, x - 70 * s, y + 200 * s);
            g.DrawLine(stand, x + 70 * s, y + 120 * s, x + 70 * s, y + 200 * s);
            g.DrawLine(stand, x - 70 * s, y + 120 * s, x + 70 * s, y + 120 * s);
        }
        using (SolidBrush bronze = new SolidBrush(C(168, 117, 48)))
        {
            g.FillEllipse(bronze, x - 78 * s, y - 78 * s, 156 * s, 156 * s);
        }
        using (Pen ring = new Pen(A(C(244, 196, 96), 160), 4))
        {
            g.DrawEllipse(ring, x - 58 * s, y - 58 * s, 116 * s, 116 * s);
            g.DrawEllipse(ring, x - 26 * s, y - 26 * s, 52 * s, 52 * s);
        }
        using (SolidBrush center = new SolidBrush(C(128, 82, 30)))
        {
            g.FillEllipse(center, x - 18 * s, y - 18 * s, 36 * s, 36 * s);
        }
    }

    static void DrawOperaMask(Graphics g, float x, float y, float s, Color color, double seed)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.RotateTransform((float)(Math.Sin(seed * 6.0) * 7.0));
        g.ScaleTransform(s, s);
        using (SolidBrush b = new SolidBrush(A(color, 210)))
        {
            g.FillEllipse(b, -42, -54, 84, 108);
        }
        using (Pen ink = new Pen(C(18, 12, 10), 4))
        {
            g.DrawEllipse(ink, -42, -54, 84, 108);
            g.DrawArc(ink, -28, -26, 22, 14, 200, 140);
            g.DrawArc(ink, 6, -26, 22, 14, 200, 140);
            g.DrawArc(ink, -18, 18, 36, 18, 20, 140);
            g.DrawLine(ink, 0, -12, 0, 14);
        }
        using (SolidBrush gold = new SolidBrush(C(230, 180, 82)))
        {
            g.FillEllipse(gold, -12, -8, 8, 5);
            g.FillEllipse(gold, 4, -8, 8, 5);
        }
        g.Restore(st);
    }

    static void DrawXiaoHe(Graphics g, float x, float y, float s, double local, double pose)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.ScaleTransform(s, s);

        // shadow
        using (SolidBrush shadow = new SolidBrush(A(C(0, 0, 0), 90)))
        {
            g.FillEllipse(shadow, -80, 120, 160, 34);
        }

        // legs
        using (Pen leg = new Pen(C(22, 16, 14), 24))
        {
            leg.StartCap = LineCap.Round;
            leg.EndCap = LineCap.Round;
            g.DrawLine(leg, -22, 75, -34, 145);
            g.DrawLine(leg, 22, 75, 40, 142);
        }

        // robe
        using (GraphicsPath robe = new GraphicsPath())
        {
            robe.AddBezier(-58, -40, -92, 40, -86, 110, -58, 130);
            robe.AddBezier(-58, 130, -20, 150, 20, 150, 58, 130);
            robe.AddBezier(58, 130, 86, 110, 92, 40, 58, -40);
            robe.CloseFigure();
            using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(-90, -50, 180, 200), C(178, 38, 34), C(88, 17, 20), 0f))
            {
                g.FillPath(b, robe);
            }
        }

        // gold sash
        using (Pen sash = new Pen(C(214, 162, 74), 12))
        {
            sash.StartCap = LineCap.Round;
            sash.EndCap = LineCap.Round;
            g.DrawLine(sash, -58, 45, 58, 60);
        }

        // arms
        using (Pen arm = new Pen(C(178, 38, 34), 20))
        {
            arm.StartCap = LineCap.Round;
            arm.EndCap = LineCap.Round;
            g.DrawLine(arm, -55, -20, -104, 5);
            g.DrawLine(arm, 55, -20, 94, -46 + (float)(pose * 10));
        }

        // hands
        using (SolidBrush skin = new SolidBrush(C(238, 198, 163)))
        {
            g.FillEllipse(skin, -116, -4, 24, 20);
            g.FillEllipse(skin, 88, -56, 24, 20);
        }

        // fan
        GraphicsState fs = g.Save();
        g.TranslateTransform(102, -58);
        g.RotateTransform(-20 + (float)(pose * 12));
        using (SolidBrush fan = new SolidBrush(C(198, 44, 38)))
        {
            GraphicsPath fp = new GraphicsPath();
            fp.AddPie(0, 0, 120, 120, 200, 140);
            g.FillPath(fan, fp);
        }
        using (Pen rib = new Pen(C(218, 166, 80), 2))
        {
            for (int i = 0; i < 5; i++)
            {
                double a = (200 + i * 28) * Math.PI / 180.0;
                g.DrawLine(rib, 0, 0, (float)(Math.Cos(a) * 120), (float)(Math.Sin(a) * 120));
            }
        }
        g.Restore(fs);

        // head
        using (SolidBrush skin = new SolidBrush(C(238, 198, 163)))
        {
            g.FillEllipse(skin, -34, -108, 68, 82);
        }

        // hair
        using (SolidBrush hair = new SolidBrush(C(18, 14, 13)))
        {
            g.FillEllipse(hair, -40, -118, 80, 54);
            g.FillRectangle(hair, -40, -92, 16, 48);
            g.FillRectangle(hair, 24, -92, 16, 48);
        }

        // opera face paint
        using (SolidBrush gold = new SolidBrush(C(226, 176, 78)))
        {
            g.FillEllipse(gold, -30, -88, 60, 48);
        }
        using (Pen ink = new Pen(C(18, 12, 10), 3))
        {
            g.DrawArc(ink, -26, -78, 22, 14, 200, 140);
            g.DrawArc(ink, 4, -78, 22, 14, 200, 140);
            g.DrawArc(ink, -18, -52, 36, 18, 20, 140);
        }
        using (SolidBrush red = new SolidBrush(C(188, 34, 30)))
        {
            g.FillPie(red, -34, -112, 22, 34, 270, 90);
            g.FillPie(red, 12, -112, 22, 34, 180, 90);
        }
        using (SolidBrush eye = new SolidBrush(C(18, 12, 10)))
        {
            g.FillEllipse(eye, -18, -74, 8, 5);
            g.FillEllipse(eye, 10, -74, 8, 5);
        }
        // mole behind left ear
        using (SolidBrush mole = new SolidBrush(C(82, 44, 32)))
        {
            g.FillEllipse(mole, -36, -60, 3, 3);
        }

        g.Restore(st);
    }

    // ---------- S04: hotpot ----------

    static void DrawHotpot(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(54, 14, 12), C(12, 8, 7), 90);
        DrawRadialGlow(g, new RectangleF(280, 100, 720, 600), C(230, 78, 34), 38);

        // table
        Grad(g, new RectangleF(0, 520, W, 200), C(70, 37, 22), C(16, 10, 8), 90);

        // hotpot outer
        using (SolidBrush metal = new SolidBrush(C(46, 44, 42)))
        {
            g.FillEllipse(metal, 260, 260, 760, 420);
        }
        using (SolidBrush inner = new SolidBrush(C(34, 30, 28)))
        {
            g.FillEllipse(inner, 292, 292, 696, 356);
        }
        // broth
        using (LinearGradientBrush broth = new LinearGradientBrush(new RectangleF(320, 320, 640, 300), C(198, 46, 28), C(92, 16, 12), 90f))
        {
            g.FillEllipse(broth, 320, 320, 640, 300);
        }

        // bubbles
        Random rnd = new Random(404);
        for (int i = 0; i < 26; i++)
        {
            float bx = 350 + (float)rnd.NextDouble() * 580;
            float by = 350 + (float)rnd.NextDouble() * 230;
            float br = 4 + (float)rnd.NextDouble() * 15;
            double phase = (t * 1.7 + i * 0.7) % 1.0;
            float r2 = br * (0.8f + (float)phase * 0.5f);
            using (SolidBrush b = new SolidBrush(Color.FromArgb(90 + rnd.Next(80), 248, 180, 92)))
            {
                g.FillEllipse(b, bx - r2, by - r2, r2 * 2, r2 * 2);
            }
        }

        // chilies
        for (int i = 0; i < 16; i++)
        {
            float x = 350 + (i * 73) % 580;
            float y = 350 + (i * 47) % 230;
            GraphicsState st = g.Save();
            g.TranslateTransform(x, y);
            g.RotateTransform(i * 23);
            using (SolidBrush chili = new SolidBrush(C(192, 30, 24)))
            {
                g.FillEllipse(chili, -18, -6, 36, 12);
            }
            using (Pen tip = new Pen(C(222, 78, 38), 2))
            {
                g.DrawLine(tip, 14, 0, 24, -4);
            }
            g.Restore(st);
        }

        // peppercorns
        for (int i = 0; i < 28; i++)
        {
            float x = 360 + (i * 61) % 560;
            float y = 360 + (i * 37) % 210;
            using (SolidBrush p = new SolidBrush(C(72, 108, 44)))
            {
                g.FillEllipse(p, x, y, 7, 6);
            }
        }

        // tripe and chopsticks
        using (SolidBrush tripe = new SolidBrush(C(216, 190, 150)))
        {
            g.FillEllipse(tripe, 720, 300, 90, 46);
        }
        using (Pen ridge = new Pen(A(C(156, 122, 86), 120), 2))
        {
            for (int i = 0; i < 4; i++)
            {
                g.DrawArc(ridge, 730 + i * 12, 306, 26, 30, 200, 140);
            }
        }
        using (Pen stick = new Pen(C(86, 55, 30), 7))
        {
            stick.StartCap = LineCap.Round;
            stick.EndCap = LineCap.Round;
            g.DrawLine(stick, 760, 330, 900, 80);
            g.DrawLine(stick, 810, 340, 950, 96);
        }

        // steam
        DrawSteam(g, 500, 330, t, 5, 190);
        DrawSteam(g, 760, 320, t + 0.6, 5, 170);

        // side dishes
        using (SolidBrush plate = new SolidBrush(C(222, 210, 188)))
        {
            g.FillEllipse(plate, 70, 560, 220, 42);
            g.FillEllipse(plate, 980, 560, 220, 42);
        }
        using (SolidBrush veg = new SolidBrush(C(66, 112, 48)))
        {
            g.FillEllipse(veg, 110, 550, 130, 34);
            g.FillEllipse(veg, 1020, 550, 130, 34);
        }

        DrawChapterMark(g, "04 / 火锅", 70, 660);
    }

    // ---------- S05: rain alley ----------

    static void DrawRainAlley(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(5, 14, 20), C(14, 33, 40), 90);

        // buildings left and right
        using (SolidBrush wall = new SolidBrush(C(22, 25, 24)))
        {
            g.FillRectangle(wall, 0, 100, 300, 520);
            g.FillRectangle(wall, 980, 100, 300, 520);
        }
        using (Pen brick = new Pen(A(C(70, 60, 48), 50), 1))
        {
            for (int i = 0; i < 14; i++)
            {
                float y = 120 + i * 36;
                g.DrawLine(brick, 0, y, 300, y);
                g.DrawLine(brick, 980, y, 1280, y);
            }
        }

        // windows
        DrawAlleyWindow(g, 60, 190, 110, 150, t);
        DrawAlleyWindow(g, 1080, 210, 110, 150, t);
        DrawAlleyWindow(g, 70, 410, 90, 120, t);
        DrawAlleyWindow(g, 1110, 390, 90, 120, t);

        // distant alley
        using (Brush path = new LinearGradientBrush(new RectangleF(300, 300, 680, 420), C(28, 57, 58), C(8, 18, 20), 90f))
        {
            g.FillRectangle(path, 300, 300, 680, 420);
        }

        // wet ground
        Grad(g, new RectangleF(0, 560, W, 160), C(14, 35, 38), C(3, 8, 10), 90);
        using (Pen reflect = new Pen(A(C(224, 66, 48), 50), 3))
        {
            g.DrawLine(reflect, 180, 620, 300, 700);
            g.DrawLine(reflect, 420, 610, 480, 700);
            g.DrawLine(reflect, 820, 610, 760, 700);
            g.DrawLine(reflect, 1080, 620, 980, 700);
        }

        // lantern strings
        using (Pen wire = new Pen(C(20, 16, 14), 2))
        {
            g.DrawLine(wire, 0, 90, W, 90);
        }
        for (int i = 0; i < 7; i++)
        {
            DrawLantern(g, 100 + i * 190, 120 + (i % 2) * 24, 0.72f, t + i * 0.2);
        }

        // figures walking away
        DrawAlleyFigure(g, 560, 540, 1.1f, C(154, 32, 30), true, local);
        DrawAlleyFigure(g, 660, 530, 1.0f, C(48, 42, 40), false, local + 0.2);
        DrawAlleyFigure(g, 750, 545, 1.05f, C(56, 50, 48), false, local + 0.4);

        // umbrella
        using (SolidBrush umb = new SolidBrush(C(184, 42, 38)))
        {
            g.FillPie(umb, 500, 380, 260, 120, 180, 180);
        }
        using (Pen rib = new Pen(C(224, 172, 80), 2))
        {
            for (int i = 0; i < 5; i++)
            {
                g.DrawLine(rib, 630, 440, 520 + i * 55, 380);
            }
        }
        using (Pen pole = new Pen(C(40, 28, 20), 4))
        {
            g.DrawLine(pole, 630, 440, 630, 560);
        }

        DrawRain(g, t, 120, new RectangleF(0, 0, W, H), 48);
        DrawChapterMark(g, "05 / 雨巷", 70, 660);
    }

    static void DrawAlleyWindow(Graphics g, float x, float y, float w, float h, double t)
    {
        using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(x, y, w, h), C(240, 176, 92), C(148, 72, 36), 90f))
        {
            g.FillRectangle(b, x, y, w, h);
        }
        using (Pen frame = new Pen(C(24, 16, 12), 5))
        {
            g.DrawRectangle(frame, x, y, w, h);
            g.DrawLine(frame, x + w / 2, y, x + w / 2, y + h);
        }
        using (SolidBrush glow = new SolidBrush(A(C(255, 190, 105), 18)))
        {
            g.FillRectangle(glow, x - 14, y - 14, w + 28, h + 28);
        }
    }

    static void DrawAlleyFigure(Graphics g, float x, float y, float s, Color coat, bool main, double local)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.ScaleTransform(s, s);

        using (SolidBrush shadow = new SolidBrush(A(C(0, 0, 0), 80)))
        {
            g.FillEllipse(shadow, -30, 50, 60, 16);
        }

        // body
        using (SolidBrush body = new SolidBrush(coat))
        {
            FillRound(g, body, new RectangleF(-22, -18, 44, 76), 16);
        }
        // legs
        using (Pen leg = new Pen(C(24, 18, 16), 10))
        {
            leg.StartCap = LineCap.Round;
            leg.EndCap = LineCap.Round;
            g.DrawLine(leg, -10, 52, -16, 92);
            g.DrawLine(leg, 10, 52, 18, 92);
        }
        // head
        using (SolidBrush skin = new SolidBrush(C(226, 184, 148)))
        {
            g.FillEllipse(skin, -16, -56, 32, 36);
        }
        using (SolidBrush hair = new SolidBrush(C(20, 16, 14)))
        {
            g.FillEllipse(hair, -18, -62, 36, 24);
        }
        if (main)
        {
            using (SolidBrush gold = new SolidBrush(C(214, 162, 74)))
            {
                g.FillRectangle(gold, -22, 10, 44, 6);
            }
        }
        g.Restore(st);
    }

    // ---------- S06: end card ----------

    static void DrawEndCard(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(12, 11, 11), C(3, 3, 4), 90);

        // subtle paper texture
        Random rnd = new Random(606);
        using (SolidBrush fiber = new SolidBrush(Color.FromArgb(10, 255, 245, 226)))
        {
            for (int i = 0; i < 900; i++)
            {
                g.FillRectangle(fiber, rnd.Next(W), rnd.Next(H), 1, 1);
            }
        }

        // red rule draws in
        double e = Ease(local);
        float ruleW = (float)(820 * e);
        using (Pen red = new Pen(C(190, 48, 38), 3))
        {
            g.DrawLine(red, 230, 214, 230 + ruleW, 214);
        }

        // mask line icon
        using (Pen gold = new Pen(C(214, 162, 74), 2.5f))
        {
            g.DrawEllipse(gold, 238, 122, 62, 70);
            g.DrawArc(gold, 252, 148, 14, 8, 200, 140);
            g.DrawArc(gold, 272, 148, 14, 8, 200, 140);
            g.DrawArc(gold, 258, 170, 22, 10, 20, 140);
            g.DrawLine(gold, 268, 132, 268, 164);
        }

        using (Font title = new Font(handFont, 78.0f, FontStyle.Bold, GraphicsUnit.Pixel))
        using (Font sub = new Font(uiFont, 28.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (Font small = new Font(uiFont, 15.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush goldText = new SolidBrush(C(232, 190, 112)))
        using (SolidBrush cream = new SolidBrush(C(246, 231, 206)))
        using (SolidBrush muted = new SolidBrush(A(C(246, 231, 206), 150)))
        {
            using (StringFormat center = new StringFormat())
            {
                center.Alignment = StringAlignment.Center;
                center.LineAlignment = StringAlignment.Center;
                g.DrawString("一碗茶，慢慢摆", title, goldText, new RectangleF(0, 250, W, 120), center);
                g.DrawString("30 秒川味实验", sub, cream, new RectangleF(0, 390, W, 50), center);
                g.DrawString("AI 写词 · Suno · ComfyUI + Seedance · CapCut", small, muted, new RectangleF(0, 548, W, 30), center);
                g.DrawString("原创川味变体 / 不使用熊猫 Rap 本体", small, muted, new RectangleF(0, 590, W, 30), center);
            }
        }

        // small gold corner marks
        using (Pen corner = new Pen(A(C(214, 162, 74), 130), 2))
        {
            g.DrawLine(corner, 70, 70, 110, 70);
            g.DrawLine(corner, 70, 70, 70, 110);
            g.DrawLine(corner, 1210, 70, 1170, 70);
            g.DrawLine(corner, 1210, 70, 1210, 110);
            g.DrawLine(corner, 70, 650, 110, 650);
            g.DrawLine(corner, 70, 650, 70, 610);
            g.DrawLine(corner, 1210, 650, 1170, 650);
            g.DrawLine(corner, 1210, 650, 1210, 610);
        }
    }

    // ---------- Shared props ----------

    static void DrawTeaLeaf(Graphics g, float x, float y, float s, double angle)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.RotateTransform((float)angle);
        using (SolidBrush leaf = new SolidBrush(C(196, 218, 160)))
        {
            GraphicsPath p = new GraphicsPath();
            p.AddBezier(0, -s, s * 0.8f, -s * 0.4f, s * 0.7f, s * 0.6f, 0, s);
            p.AddBezier(0, s, -s * 0.7f, s * 0.6f, -s * 0.8f, -s * 0.4f, 0, -s);
            g.FillPath(leaf, p);
        }
        using (Pen vein = new Pen(A(C(56, 92, 48), 160), 1.4f))
        {
            g.DrawLine(vein, 0, -s, 0, s);
        }
        g.Restore(st);
    }

    static void DrawChapterMark(Graphics g, string text, float x, float y)
    {
        using (Font f = new Font(uiFont, 14.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 120)))
        {
            g.DrawString(text, f, b, x, y);
        }
    }

    static void DrawReflections(Graphics g, double t, int unused)
    {
        using (SolidBrush warm = new SolidBrush(A(C(235, 112, 54), 24)))
        {
            g.FillRectangle(warm, 620, 540, 120, 150);
            g.FillRectangle(warm, 900, 545, 90, 140);
            g.FillRectangle(warm, 1120, 550, 70, 120);
        }
        using (SolidBrush cool = new SolidBrush(A(C(110, 180, 200), 16)))
        {
            g.FillRectangle(cool, 180, 545, 70, 150);
        }
        using (Pen p = new Pen(A(C(255, 210, 150), 18), 2))
        {
            for (int i = 0; i < 8; i++)
            {
                float x = 600 + i * 52;
                g.DrawLine(p, x, 560, x + (float)Math.Sin(t + i) * 7, 700);
            }
        }
    }

    // ---------- Post ----------

    static void DrawVignette(Graphics g)
    {
        using (GraphicsPath path = new GraphicsPath())
        {
            path.AddRectangle(new RectangleF(0, 0, W, H));
            using (PathGradientBrush b = new PathGradientBrush(path))
            {
                b.CenterPoint = new PointF(W / 2.0f, H / 2.0f);
                b.CenterColor = Color.Transparent;
                b.SurroundColors = new Color[] { Color.FromArgb(150, 0, 0, 0) };
                g.FillPath(b, path);
            }
        }
    }

    static void DrawGrain(Graphics g, double t)
    {
        Random rnd = new Random((int)(t * 1000) + 991);
        using (SolidBrush b = new SolidBrush(Color.FromArgb(9, 255, 255, 255)))
        {
            for (int i = 0; i < 420; i++)
            {
                g.FillRectangle(b, rnd.Next(W), rnd.Next(H), 1, 1);
            }
        }
    }

    // ---------- Assets ----------

    static void GenerateAssets()
    {
        RenderStill(Path.Combine(assetsDir, "characters", "xiaohe_sheet.png"), 1600, 900, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, 1600, 900), C(30, 18, 16), C(10, 9, 9), 90);
            using (Font f = new Font(uiFont, 36.0f, FontStyle.Bold, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(C(246, 231, 206)))
            {
                g.DrawString("小禾 / 角色定妆表", f, b, 70, 50);
            }
            using (Font f = new Font(uiFont, 18.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 180)))
            {
                g.DrawString("短黑发 · 红黑戏服 · 金色脸谱 · 耳后小痣", f, b, 74, 104);
            }
            DrawXiaoHe(g, 320, 780, 2.2f, 0.2, 0.3);
            DrawXiaoHe(g, 790, 780, 2.2f, 0.5, 0.7);
            DrawXiaoHe(g, 1240, 780, 2.2f, 0.8, 0.5);
            using (Font f = new Font(uiFont, 16.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 160)))
            {
                g.DrawString("正面 / 变脸 / 收势", f, b, 250, 840);
                g.DrawString("正面 / 变脸 / 收势", f, b, 720, 840);
                g.DrawString("正面 / 变脸 / 收势", f, b, 1170, 840);
            }
        });

        RenderStill(Path.Combine(assetsDir, "scenes", "teahouse_rain.png"), W, H, delegate(Graphics g)
        {
            DrawTeahouseWide(g, 0.2, 0.5);
        });

        RenderStill(Path.Combine(assetsDir, "scenes", "alley_night.png"), W, H, delegate(Graphics g)
        {
            DrawRainAlley(g, 0.2, 0.5);
        });

        RenderStill(Path.Combine(assetsDir, "props", "gaiwan.png"), 1000, 700, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, 1000, 700), C(44, 27, 18), C(10, 9, 8), 90);
            DrawGaiwan(g, 500, 420, 3.2f, 0, false);
            DrawWarmRim(g, 300, 220, 400, 380, 0.14);
        });

        RenderStill(Path.Combine(outputDir, "cover.png"), W, H, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, W, H), C(10, 18, 20), C(45, 20, 16), 90);
            DrawRadialGlow(g, new RectangleF(360, 70, 560, 560), C(255, 190, 100), 34);
            using (Font title = new Font(handFont, 72.0f, FontStyle.Bold, GraphicsUnit.Pixel))
            using (Font sub = new Font(uiFont, 26.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (Font small = new Font(uiFont, 14.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush gold = new SolidBrush(C(232, 190, 112)))
            using (SolidBrush cream = new SolidBrush(C(246, 231, 206)))
            using (SolidBrush muted = new SolidBrush(A(C(246, 231, 206), 150)))
            {
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString("一碗茶，慢慢摆", title, gold, new RectangleF(0, 230, W, 110), sf);
                    g.DrawString("30 秒川味实验 / 原创变体", sub, cream, new RectangleF(0, 360, W, 50), sf);
                    g.DrawString("AI 写词 · Suno · ComfyUI + Seedance · CapCut", small, muted, new RectangleF(0, 640, W, 30), sf);
                }
            }
        });
    }

    static void RenderStill(string path, int w, int h, Action<Graphics> draw)
    {
        using (Bitmap bmp = new Bitmap(w, h))
        using (Graphics g = Graphics.FromImage(bmp))
        {
            SetupGraphics(g);
            draw(g);
            bmp.Save(path, ImageFormat.Png);
        }
    }

    // ---------- Helpers ----------

    static Color C(int r, int g, int b)
    {
        return Color.FromArgb(r, g, b);
    }

    static Color A(Color c, int a)
    {
        if (a < 0) a = 0;
        if (a > 255) a = 255;
        return Color.FromArgb(a, c.R, c.G, c.B);
    }

    static double Clamp01(double x)
    {
        if (x < 0) return 0;
        if (x > 1) return 1;
        return x;
    }

    static double Ease(double x)
    {
        x = Clamp01(x);
        return x * x * (3.0 - 2.0 * x);
    }

    static double FadeIn(double t, double a, double b)
    {
        if (t <= a) return 0;
        if (t >= b) return 1;
        return Clamp01((t - a) / (b - a));
    }

    static double FadeOut(double t, double a, double b)
    {
        if (t <= a) return 1;
        if (t >= b) return 0;
        return 1.0 - Clamp01((t - a) / (b - a));
    }

    static void Grad(Graphics g, RectangleF r, Color c1, Color c2, float angle)
    {
        using (LinearGradientBrush b = new LinearGradientBrush(r, c1, c2, angle))
        {
            g.FillRectangle(b, r);
        }
    }

    static GraphicsPath RoundPath(RectangleF r, float radius)
    {
        float d = Math.Min(Math.Max(1.0f, radius * 2.0f), Math.Min(r.Width, r.Height));
        GraphicsPath p = new GraphicsPath();
        p.AddArc(r.X, r.Y, d, d, 180, 90);
        p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
        p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
        p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
        p.CloseFigure();
        return p;
    }

    static void FillRound(Graphics g, Brush b, RectangleF r, float radius)
    {
        using (GraphicsPath p = RoundPath(r, radius))
        {
            g.FillPath(b, p);
        }
    }

    static void DrawSteam(Graphics g, float x, float y, double t, int count, float height)
    {
        using (Pen p = new Pen(A(C(255, 255, 255), 38), 2.0f))
        {
            for (int i = 0; i < count; i++)
            {
                float ox = (i - (count - 1) * 0.5f) * 10.0f;
                float phase = (float)(t * 1.3 + i * 0.8);
                float sway = (float)Math.Sin(phase) * 10.0f;
                using (GraphicsPath path = new GraphicsPath())
                {
                    path.AddBezier(x + ox, y, x + ox + 12 + sway, y - height * 0.3f, x + ox - 12 + sway, y - height * 0.65f, x + ox + 4, y - height);
                    g.DrawPath(p, path);
                }
            }
        }
    }

    static void DrawRadialGlow(Graphics g, RectangleF r, Color color, int alpha)
    {
        using (GraphicsPath path = new GraphicsPath())
        {
            path.AddEllipse(r);
            using (PathGradientBrush b = new PathGradientBrush(path))
            {
                b.CenterPoint = new PointF(r.X + r.Width / 2.0f, r.Y + r.Height / 2.0f);
                b.CenterColor = A(color, alpha);
                b.SurroundColors = new Color[] { A(color, 0) };
                g.FillPath(b, path);
            }
        }
    }

    static void DrawBokeh(Graphics g, double local, int count, Color color, double alphaScale)
    {
        Random rnd = new Random(1212);
        for (int i = 0; i < count; i++)
        {
            float x = (float)rnd.NextDouble() * W;
            float y = (float)rnd.NextDouble() * H * 0.7f;
            float r = 16 + (float)rnd.NextDouble() * 70;
            int a = (int)((8 + rnd.Next(30)) * alphaScale * 4.0);
            using (SolidBrush b = new SolidBrush(Color.FromArgb(Math.Min(90, a), color.R, color.G, color.B)))
            {
                g.FillEllipse(b, x - r, y - r, r * 2, r * 2);
            }
        }
    }

    static void DrawWarmRim(Graphics g, float x, float y, float w, float h, double alpha)
    {
        using (Pen p = new Pen(A(C(255, 210, 150), (int)(alpha * 255)), 2))
        {
            g.DrawArc(p, x, y, w, h, -50, 70);
        }
    }

    static void SaveJpeg(Bitmap bmp, string path, long quality)
    {
        ImageCodecInfo codec = GetEncoder(ImageFormat.Jpeg);
        EncoderParameters p = new EncoderParameters(1);
        p.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, quality);
        bmp.Save(path, codec, p);
    }

    static ImageCodecInfo GetEncoder(ImageFormat format)
    {
        ImageCodecInfo[] codecs = ImageCodecInfo.GetImageDecoders();
        foreach (ImageCodecInfo codec in codecs)
        {
            if (codec.FormatID == format.Guid) return codec;
        }
        return null;
    }
}
