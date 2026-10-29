using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Text;

class DemoRenderer
{
    const int W = 1280;
    const int H = 720;
    const int FPS = 30;
    const double DURATION = 24.0;

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
            if (f % 60 == 0) Console.WriteLine("  frame " + f + "/" + total);
        }

        Console.WriteLine("Generating beat...");
        BeatGenerator.Generate(Path.Combine(audioDir, "beat.wav"), DURATION);

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
        int shot = Math.Min(7, (int)(t / 3.0));
        double local = (t - shot * 3.0) / 3.0;
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
            case 0: zoom = 1.00 + 0.05 * e; panY = 2.0 * e; break;
            case 1: zoom = 1.02 + 0.05 * e; panY = -8.0 * e; break;
            case 2: zoom = 1.04 + 0.04 * e; panX = -18.0 + 36.0 * e; break;
            case 3: zoom = 1.01 + 0.04 * e; panX = -6.0 * e; break;
            case 4: zoom = 1.02 + 0.05 * e; panY = -4.0 * e; break;
            case 5: zoom = 1.00 + 0.06 * e; panX = 8.0 * e; break;
            case 6: zoom = 1.01 + 0.06 * e; panY = -3.0 * e; break;
            case 7: zoom = 1.08 - 0.08 * e; break;
        }
    }

    static void DrawShot(Graphics g, int shot, double local, double t)
    {
        switch (shot)
        {
            case 0: DrawCafeWide(g, local, t); break;
            case 1: DrawEspresso(g, local, t); break;
            case 2: DrawBaristaCounter(g, local, t); break;
            case 3: DrawWindowRain(g, local, t); break;
            case 4: DrawCupSleeve(g, local, t); break;
            case 5: DrawStreetScene(g, local, t, true, 710, 0.98f, "wait", local); break;
            case 6: DrawCupNote(g, local, t); break;
            case 7: DrawEnding(g, local, t); break;
        }
    }

    // ---------- Subtitles ----------

    static readonly string[] SubTexts = new string[]
    {
        "清晨六点半 街角灯还亮",
        "第一杯咖啡 等一个晚到的人",
        "雨点敲着窗 秒针走得慢",
        "我把你的名字 写在杯套上",
        "晚到也算到 热着就好",
        "街角这盏灯 替你留着",
        "明天 早点来"
    };

    static readonly double[] SubStart = new double[] { 2.0, 5.2, 9.0, 12.5, 16.0, 18.6, 21.5 };
    static readonly double[] SubEnd = new double[] { 5.2, 8.8, 12.4, 15.8, 18.6, 21.2, 23.0 };

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
            using (SolidBrush bg = new SolidBrush(Color.FromArgb((int)(135.0 * alpha), 0, 0, 0)))
            {
                using (GraphicsPath p = RoundPath(box, 12.0f)) g.FillPath(bg, p);
            }
            using (SolidBrush b = new SolidBrush(Color.FromArgb((int)(255.0 * alpha), 255, 255, 255)))
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

    // ---------- S01 ----------

    static void DrawCafeWide(Graphics g, double local, double t)
    {
        DrawCafeBase(g, t, true, "counter", local);
        DrawForegroundCup(g, 270, 535, 1.05f, t);
        DrawTitleMark(g, "06:30", 80, 640);
    }

    // ---------- S02 ----------

    static void DrawEspresso(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(20, 12, 8), C(8, 6, 6), 90);
        DrawBokeh(g, local, 18, C(242, 181, 107), 0.16);

        Grad(g, new RectangleF(0, 520, W, 200), C(48, 30, 20), C(12, 8, 6), 90);
        using (Pen p = new Pen(A(C(255, 210, 150), 40), 2))
        {
            g.DrawLine(p, 0, 520, W, 520);
        }

        // portafilter
        using (SolidBrush body = new SolidBrush(C(36, 36, 34)))
        {
            FillRound(g, body, new RectangleF(520, 120, 240, 42), 16);
        }
        using (SolidBrush brass = new SolidBrush(C(176, 126, 62)))
        {
            FillRound(g, brass, new RectangleF(540, 150, 200, 10), 5);
        }
        using (Pen handle = new Pen(C(75, 43, 25), 18))
        {
            handle.EndCap = LineCap.Round;
            g.DrawLine(handle, 760, 140, 920, 112);
        }

        // espresso stream
        using (Pen stream = new Pen(C(92, 48, 22), 5))
        {
            stream.EndCap = LineCap.Round;
            g.DrawLine(stream, 640, 160, 640, 352);
        }
        using (SolidBrush drop = new SolidBrush(C(120, 64, 28)))
        {
            g.FillEllipse(drop, 635, 350, 10, 14);
        }

        // saucer
        using (SolidBrush saucer = new SolidBrush(C(238, 222, 196)))
        {
            g.FillEllipse(saucer, 470, 535, 340, 64);
        }
        using (SolidBrush saucer2 = new SolidBrush(C(210, 190, 160)))
        {
            g.FillEllipse(saucer2, 500, 548, 280, 36);
        }

        // cup
        using (GraphicsPath cup = new GraphicsPath())
        {
            cup.AddBezier(540, 365, 535, 470, 560, 535, 640, 535);
            cup.AddBezier(640, 535, 720, 535, 745, 470, 740, 365);
            cup.CloseFigure();
            using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(535, 360, 210, 180), C(255, 244, 220), C(206, 184, 150), 0f))
                g.FillPath(b, cup);
        }
        using (Pen rim = new Pen(C(255, 248, 230), 4))
        {
            g.DrawArc(rim, 540, 360, 200, 34, 180, 180);
        }
        using (SolidBrush crema = new SolidBrush(C(176, 112, 56)))
        {
            g.FillEllipse(crema, 562, 364, 156, 26);
        }
        using (Pen swirl = new Pen(A(C(255, 220, 170), 130), 2))
        {
            g.DrawArc(swirl, 590, 368, 100, 16, 10, 210);
            g.DrawArc(swirl, 615, 371, 56, 10, 200, 160);
        }
        using (Pen handle = new Pen(C(230, 210, 180), 12))
        {
            g.DrawArc(handle, 720, 410, 58, 70, -90, 180);
        }

        DrawSteam(g, 640, 350, t, 5, 150);
        DrawWarmRim(g, 520, 350, 280, 200, 0.15);

        using (Font f = new Font(handFont, 20.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(A(C(255, 230, 190), 150)))
        {
            g.DrawString("first cup", f, b, 70, 86);
        }
    }

    // ---------- S03 ----------

    static void DrawBaristaCounter(Graphics g, double local, double t)
    {
        DrawCafeBase(g, t, true, "counter", local);
        DrawForegroundCup(g, 330, 540, 0.9f, t);
    }

    // ---------- S04 ----------

    static void DrawWindowRain(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(8, 20, 31), C(18, 46, 63), 90);

        RectangleF frame = new RectangleF(60, 36, 1160, 648);
        using (SolidBrush wood = new SolidBrush(C(22, 16, 13)))
        {
            g.FillRectangle(wood, frame);
        }
        RectangleF glass = new RectangleF(92, 68, 1096, 584);
        using (LinearGradientBrush b = new LinearGradientBrush(glass, C(29, 77, 109), C(119, 167, 196), 90f))
        {
            g.FillRectangle(b, glass);
        }

        // city bokeh
        Random rnd = new Random(401);
        for (int i = 0; i < 42; i++)
        {
            float x = glass.X + (float)rnd.NextDouble() * glass.Width;
            float y = glass.Y + glass.Height * 0.45f + (float)rnd.NextDouble() * glass.Height * 0.5f;
            float r = 3.0f + (float)rnd.NextDouble() * 14.0f;
            int a = 20 + rnd.Next(50);
            using (SolidBrush b = new SolidBrush(Color.FromArgb(a, 255, 206, 140)))
            {
                g.FillEllipse(b, x - r, y - r, r * 2, r * 2);
            }
        }

        // window mullions
        using (Pen p = new Pen(C(32, 20, 14), 12))
        {
            g.DrawLine(p, glass.X + glass.Width / 2, glass.Y, glass.X + glass.Width / 2, glass.Bottom);
            g.DrawLine(p, glass.X, glass.Y + glass.Height * 0.56f, glass.Right, glass.Y + glass.Height * 0.56f);
        }

        // rain streaks
        for (int i = 0; i < 90; i++)
        {
            double seed = i * 12.9898;
            double sx = (seed * 43758.5453) % 1.0;
            double sy = ((seed + 7.13) * 24634.6345) % 1.0;
            float x = glass.X + (float)(sx * glass.Width);
            float y = glass.Y + (float)(((sy + t * 0.22) % 1.0) * glass.Height);
            float len = 10.0f + (float)((i * 7) % 22);
            using (Pen p = new Pen(A(C(220, 240, 255), 45 + (i % 4) * 12), 1.2f))
            {
                g.DrawLine(p, x, y, x - 3.0f, y + len);
            }
        }

        // reflection of Xiaoman in glass
        using (SolidBrush sil = new SolidBrush(A(C(246, 231, 206), 26)))
        {
            g.FillEllipse(sil, 890, 250, 92, 108);
            FillRound(g, sil, new RectangleF(850, 340, 174, 220), 40);
            g.FillEllipse(sil, 930, 220, 60, 70);
        }

        // warm interior reflection
        using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(92, 68, 420, 584), A(C(242, 181, 107), 78), A(C(242, 181, 107), 0), 0f))
        {
            g.FillRectangle(b, 92, 68, 420, 584);
        }

        // vignette on glass
        using (SolidBrush b = new SolidBrush(A(C(4, 10, 16), 100)))
        {
            g.FillRectangle(b, 92, 68, 1096, 28);
            g.FillRectangle(b, 92, 624, 1096, 28);
        }

        DrawSteam(g, 360, 470, t, 3, 90);
    }

    // ---------- S05 ----------

    static void DrawCupSleeve(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(44, 27, 18), C(10, 9, 8), 90);
        DrawBokeh(g, local, 14, C(242, 181, 107), 0.12);

        // counter
        Grad(g, new RectangleF(0, 470, W, 250), C(88, 55, 32), C(30, 18, 12), 90);
        using (Pen p = new Pen(A(C(255, 220, 170), 40), 2))
        {
            g.DrawLine(p, 0, 470, W, 470);
        }

        DrawCup(g, 690, 430, 2.25f, "", t);

        // sleeve with handwriting
        RectangleF sleeve = new RectangleF(585, 405, 210, 105);
        using (SolidBrush b = new SolidBrush(C(186, 141, 91)))
        {
            FillRound(g, b, sleeve, 8);
        }
        using (Pen p = new Pen(A(C(105, 72, 42), 120), 1.5f))
        {
            g.DrawRectangle(p, sleeve.X, sleeve.Y, sleeve.Width, sleeve.Height);
        }

        string note = "给晚到的人";
        int visible = (int)Math.Min(note.Length, Math.Floor(local * 9.0));
        string partial = note.Substring(0, Math.Max(0, visible));
        if (partial.Length > 0)
        {
            GraphicsState st = g.Save();
            g.TranslateTransform(690, 455);
            g.RotateTransform(-7.0f);
            using (Font f = new Font(handFont, 30.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(C(30, 22, 18)))
            {
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString(partial, f, b, new RectangleF(-100, -38, 200, 76), sf);
                }
            }
            g.Restore(st);
        }

        // forearms + hands (simplified, no detailed fingers)
        using (Pen arm = new Pen(C(238, 198, 163), 30))
        {
            arm.StartCap = LineCap.Round;
            arm.EndCap = LineCap.Round;
            g.DrawLine(arm, 390, 700, 520, 505);
            g.DrawLine(arm, 930, 700, 845, 460);
        }
        DrawHand(g, 520, 500, 1.15f, 18.0f);
        DrawHand(g, 845, 455, 1.0f, -22.0f);
        using (Pen pen = new Pen(C(32, 28, 25), 7))
        {
            pen.EndCap = LineCap.Round;
            g.DrawLine(pen, 805, 450, 735, 485);
        }
        using (SolidBrush tip = new SolidBrush(C(18, 16, 15)))
        {
            g.FillEllipse(tip, 728, 480, 12, 12);
        }

        DrawSteam(g, 690, 360, t, 4, 120);
        DrawWarmRim(g, 550, 330, 300, 250, 0.12);
    }

    // ---------- S06 ----------

    static void DrawStreetScene(Graphics g, double local, double t, bool character, float charX, float charScale, string pose, double charLocal)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(5, 12, 21), C(16, 38, 56), 90);

        // distant buildings
        using (SolidBrush b = new SolidBrush(C(8, 18, 27)))
        {
            g.FillRectangle(b, 0, 180, W, 300);
            for (int i = 0; i < 12; i++)
            {
                float bx = i * 120 - 30;
                float bh = 60 + (i * 47) % 150;
                g.FillRectangle(b, bx, 260 - bh, 94, bh + 40);
            }
        }
        // far windows
        Random rnd = new Random(606);
        for (int i = 0; i < 40; i++)
        {
            float x = rnd.Next(0, W);
            float y = rnd.Next(160, 380);
            using (SolidBrush b = new SolidBrush(A(C(242, 181, 107), 25 + rnd.Next(35))))
            {
                g.FillRectangle(b, x, y, 4, 6);
            }
        }

        // street lamp
        using (Pen pole = new Pen(C(20, 26, 29), 9))
        {
            g.DrawLine(pole, 220, 130, 220, 660);
            g.DrawLine(pole, 220, 130, 280, 130);
        }
        DrawRadialGlow(g, new RectangleF(100, 55, 260, 260), C(255, 200, 120), 34);
        using (SolidBrush lamp = new SolidBrush(C(255, 224, 170)))
        {
            g.FillEllipse(lamp, 258, 120, 44, 26);
        }
        using (GraphicsPath cone = new GraphicsPath())
        {
            cone.AddPolygon(new PointF[] { new PointF(258, 140), new PointF(300, 140), new PointF(460, 680), new PointF(60, 680) });
            using (SolidBrush b = new SolidBrush(A(C(255, 214, 150), 13)))
            {
                g.FillPath(b, cone);
            }
        }

        // side wall so the character reads as standing outside, under the awning
        using (SolidBrush wall = new SolidBrush(C(16, 20, 22)))
        {
            g.FillRectangle(wall, 640, 230, 120, 360);
            g.FillRectangle(wall, 640, 230, 6, 360);
        }

        // café storefront
        RectangleF shop = new RectangleF(760, 230, 450, 360);
        using (SolidBrush b = new SolidBrush(C(26, 19, 16)))
        {
            FillRound(g, b, shop, 8);
        }
        RectangleF win = new RectangleF(790, 290, 390, 220);
        using (LinearGradientBrush b = new LinearGradientBrush(win, C(242, 181, 107), C(120, 66, 35), 90f))
        {
            g.FillRectangle(b, win);
        }
        using (Pen frame = new Pen(C(36, 24, 18), 8))
        {
            g.DrawRectangle(frame, win.X, win.Y, win.Width, win.Height);
            g.DrawLine(frame, win.X + win.Width * 0.62f, win.Y, win.X + win.Width * 0.62f, win.Bottom);
        }
        // awning
        using (SolidBrush b = new SolidBrush(C(126, 48, 42)))
        {
            g.FillRectangle(b, 650, 252, 574, 34);
        }
        using (Pen p = new Pen(C(70, 26, 24), 3))
        {
            for (int i = 0; i < 10; i++) g.DrawLine(p, 660 + i * 56, 252, 660 + i * 56, 286);
        }
        // sign
        using (SolidBrush b = new SolidBrush(C(28, 20, 16)))
        {
            FillRound(g, b, new RectangleF(820, 200, 330, 38), 6);
        }
        using (Font f = new Font(uiFont, 20.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(C(246, 231, 206)))
        {
            using (StringFormat sf = new StringFormat())
            {
                sf.Alignment = StringAlignment.Center;
                sf.LineAlignment = StringAlignment.Center;
                g.DrawString("街角咖啡馆", f, b, new RectangleF(820, 200, 330, 38), sf);
            }
        }

        // wet pavement
        Grad(g, new RectangleF(0, 560, W, 160), C(24, 38, 46), C(5, 9, 13), 90);
        DrawReflections(g, t);

        // character
        if (character) DrawXiaoman(g, charX, 590, charScale, pose, charLocal);

        // rain
        for (int i = 0; i < 120; i++)
        {
            double sx = ((i * 37.17) % 1.0);
            double sy = ((i * 13.73 + t * 0.55) % 1.0);
            float x = (float)(sx * W);
            float y = (float)(sy * H);
            float len = 8.0f + (i % 5) * 9.0f;
            using (Pen p = new Pen(A(C(190, 220, 240), 28 + (i % 3) * 10), 1.0f))
            {
                g.DrawLine(p, x, y, x - 4, y + len);
            }
        }

        // puddles
        using (SolidBrush b = new SolidBrush(A(C(255, 210, 150), 16)))
        {
            g.FillEllipse(b, 130, 640, 260, 22);
            g.FillEllipse(b, 760, 650, 390, 26);
        }
    }

    static void DrawStreetWide(Graphics g, double local, double t)
    {
        DrawStreetScene(g, local, t, true, 710, 0.98f, "wait", local);
    }

    // ---------- S07 ----------

    static void DrawCupNote(Graphics g, double local, double t)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(7, 17, 27), C(50, 30, 21), 90);
        DrawBokeh(g, local, 22, C(242, 181, 107), 0.15);

        // warm café window behind the cups
        using (SolidBrush frame = new SolidBrush(C(28, 18, 14)))
        {
            FillRound(g, frame, new RectangleF(390, 60, 560, 420), 10);
        }
        RectangleF glass = new RectangleF(410, 80, 520, 380);
        using (LinearGradientBrush b = new LinearGradientBrush(glass, C(242, 181, 107), C(112, 58, 32), 90f))
        {
            g.FillRectangle(b, glass);
        }
        using (Pen mullion = new Pen(C(36, 22, 16), 10))
        {
            g.DrawLine(mullion, glass.X + glass.Width / 2, glass.Y, glass.X + glass.Width / 2, glass.Bottom);
        }
        using (Pen rain = new Pen(A(C(220, 240, 255), 35), 1.2f))
        {
            for (int i = 0; i < 28; i++)
            {
                float x = glass.X + ((i * 83) % (int)glass.Width);
                float y = glass.Y + ((i * 47) % (int)glass.Height);
                g.DrawLine(rain, x, y, x - 3, y + 14);
            }
        }
        using (SolidBrush b = new SolidBrush(A(C(255, 224, 170), 20)))
        {
            g.FillRectangle(b, glass.X, glass.Y, glass.Width, 40);
        }

        // ledge
        Grad(g, new RectangleF(0, 500, W, 220), C(44, 31, 24), C(12, 9, 8), 90);
        using (Pen p = new Pen(A(C(255, 220, 170), 30), 2))
        {
            g.DrawLine(p, 0, 500, W, 500);
        }

        DrawCup(g, 520, 450, 1.8f, "", t);
        DrawCup(g, 760, 455, 2.0f, "给晚到的人", t);

        // droplets on ledge
        Random rnd = new Random(707);
        for (int i = 0; i < 26; i++)
        {
            float x = (float)rnd.NextDouble() * W;
            float y = 520 + (float)rnd.NextDouble() * 140;
            float r = 2 + (float)rnd.NextDouble() * 5;
            using (SolidBrush b = new SolidBrush(A(C(190, 220, 240), 40)))
            {
                g.FillEllipse(b, x, y, r, r);
            }
        }

        DrawSteam(g, 760, 360, t, 5, 140);
        DrawWarmRim(g, 600, 330, 360, 260, 0.12);
    }

    // ---------- S08 ----------

    static void DrawEnding(Graphics g, double local, double t)
    {
        DrawStreetScene(g, local, t, true, 760, 0.98f, "lift", local);

        // warm arrival glow from off-screen right
        using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(980, 200, 300, 400), A(C(255, 214, 150), 80), A(C(255, 214, 150), 0), 0f))
        {
            g.FillRectangle(b, 980, 200, 300, 400);
        }

        double a = Clamp01((local - 0.54) / 0.12);
        if (a > 0.0)
        {
            using (SolidBrush b = new SolidBrush(Color.FromArgb((int)(250 * a), 10, 24, 26)))
            {
                g.FillRectangle(b, 0, 0, W, H);
            }
            DrawRadialGlow(g, new RectangleF(390, 130, 500, 360), C(255, 190, 100), (int)(24 * a));
            int alpha = (int)(255 * a);
            using (Font title = new Font(uiFont, 64.0f, FontStyle.Bold, GraphicsUnit.Pixel))
            using (Font sub = new Font(uiFont, 28.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (Font small = new Font(uiFont, 14.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush white = new SolidBrush(Color.FromArgb(alpha, 246, 231, 206)))
            using (SolidBrush amber = new SolidBrush(Color.FromArgb(alpha, 242, 181, 107)))
            {
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString("晚到也算到", title, white, new RectangleF(0, 250, W, 100), sf);
                    g.DrawString("街角咖啡馆 · 明天，早点来", sub, amber, new RectangleF(0, 370, W, 60), sf);
                    g.DrawString("LOCAL DEMO / 2026", small, new SolidBrush(Color.FromArgb((int)(alpha * 0.55), 246, 231, 206)), new RectangleF(0, 640, W, 30), sf);
                }
            }
            using (Pen line = new Pen(Color.FromArgb((int)(alpha * 0.6), 242, 181, 107), 2))
            {
                g.DrawLine(line, W / 2 - 40, 350, W / 2 + 40, 350);
            }
        }
    }

    // ---------- Shared café ----------

    static void DrawCafeBase(Graphics g, double t, bool character, string pose, double charLocal)
    {
        Grad(g, new RectangleF(0, 0, W, H), C(8, 24, 26), C(48, 28, 19), 90);
        Grad(g, new RectangleF(0, 0, W, 500), C(14, 42, 44), C(35, 27, 21), 90);
        Grad(g, new RectangleF(0, 470, W, 250), C(35, 22, 14), C(8, 6, 5), 90);

        // floor lines
        for (int i = 0; i < 7; i++)
        {
            using (Pen p = new Pen(A(C(210, 160, 110), 18), 1))
            {
                g.DrawLine(p, 640, 470, -200 + i * 300, 720);
            }
        }

        DrawWindow(g, new RectangleF(70, 80, 430, 440), t);
        DrawShelves(g, new RectangleF(880, 100, 330, 380), t);
        DrawDoor(g, new RectangleF(1170, 220, 90, 250), t);
        DrawLamp(g, 270, 60, 100, t);
        DrawLamp(g, 640, 45, 120, t);
        DrawLamp(g, 1010, 65, 105, t);
        DrawClock(g, 1150, 170, 38);

        if (character) DrawXiaoman(g, 830, 500, 1.0f, pose, charLocal);

        DrawCounter(g, new RectangleF(230, 470, 1050, 250), t);
        DrawEspressoMachine(g, 620, 400, t);
        DrawDust(g, t);
    }

    static void DrawWindow(Graphics g, RectangleF r, double t)
    {
        using (SolidBrush glow = new SolidBrush(A(C(120, 180, 220), 16)))
        {
            g.FillRectangle(glow, RectangleF.Inflate(r, 32, 32));
        }
        using (SolidBrush frame = new SolidBrush(C(28, 18, 12)))
        {
            g.FillRectangle(frame, r);
        }
        RectangleF glass = new RectangleF(r.X + 14, r.Y + 14, r.Width - 28, r.Height - 28);
        using (LinearGradientBrush b = new LinearGradientBrush(glass, C(28, 80, 112), C(150, 190, 210), 90f))
        {
            g.FillRectangle(b, glass);
        }

        using (SolidBrush city = new SolidBrush(A(C(12, 32, 46), 180)))
        {
            g.FillRectangle(city, glass.X, glass.Y + glass.Height * 0.62f, glass.Width, glass.Height * 0.38f);
            for (int i = 0; i < 10; i++)
            {
                float bx = glass.X + 10 + i * 40;
                float bh = 30 + (i * 37) % 80;
                g.FillRectangle(city, bx, glass.Y + glass.Height * 0.62f - bh, 28, bh);
            }
        }

        for (int i = 0; i < 40; i++)
        {
            float x = glass.X + ((i * 97) % (int)glass.Width);
            float y = glass.Y + ((i * 53 + (int)(t * 80)) % (int)glass.Height);
            using (Pen p = new Pen(A(Color.White, 35), 1))
            {
                g.DrawLine(p, x, y, x - 4, y + 18);
            }
        }

        using (Pen p = new Pen(C(35, 22, 14), 10))
        {
            g.DrawLine(p, r.X + r.Width / 2, r.Y, r.X + r.Width / 2, r.Bottom);
            g.DrawLine(p, r.X, r.Y + r.Height * 0.55f, r.Right, r.Y + r.Height * 0.55f);
        }
        using (Pen p = new Pen(A(Color.White, 50), 2))
        {
            g.DrawRectangle(p, glass.X, glass.Y, glass.Width, glass.Height);
        }
        using (SolidBrush b = new SolidBrush(A(C(242, 181, 107), 14)))
        {
            g.FillRectangle(b, glass.X, glass.Y, glass.Width * 0.45f, glass.Height);
        }
    }

    static void DrawShelves(Graphics g, RectangleF r, double t)
    {
        using (SolidBrush wood = new SolidBrush(C(46, 28, 18)))
        {
            g.FillRectangle(wood, r);
        }
        for (int s = 0; s < 3; s++)
        {
            float y = r.Y + 70 + s * 105;
            using (SolidBrush b = new SolidBrush(C(87, 54, 32)))
            {
                g.FillRectangle(b, r.X + 10, y, r.Width - 20, 10);
            }
            for (int i = 0; i < 6; i++)
            {
                float x = r.X + 28 + i * 46;
                using (SolidBrush cup = new SolidBrush(C(246, 231, 206)))
                {
                    g.FillEllipse(cup, x, y - 22, 28, 18);
                    g.FillRectangle(cup, x + 3, y - 12, 22, 14);
                }
            }
        }
        // plant
        using (SolidBrush pot = new SolidBrush(C(126, 74, 48)))
        {
            g.FillRectangle(pot, r.X + 250, r.Y + 250, 50, 42);
        }
        using (Pen stem = new Pen(C(55, 92, 55), 4))
        {
            g.DrawLine(stem, r.X + 275, r.Y + 250, r.X + 275, r.Y + 200);
            g.DrawLine(stem, r.X + 275, r.Y + 220, r.X + 250, r.Y + 195);
            g.DrawLine(stem, r.X + 275, r.Y + 230, r.X + 300, r.Y + 205);
        }
        using (SolidBrush leaf = new SolidBrush(C(56, 104, 62)))
        {
            g.FillEllipse(leaf, r.X + 240, r.Y + 185, 26, 16);
            g.FillEllipse(leaf, r.X + 290, r.Y + 195, 26, 16);
            g.FillEllipse(leaf, r.X + 262, r.Y + 170, 26, 16);
        }
    }

    static void DrawDoor(Graphics g, RectangleF r, double t)
    {
        using (SolidBrush frame = new SolidBrush(C(26, 18, 13)))
        {
            g.FillRectangle(frame, r);
        }
        RectangleF glass = new RectangleF(r.X + 10, r.Y + 10, r.Width - 20, r.Height - 20);
        using (LinearGradientBrush b = new LinearGradientBrush(glass, C(84, 122, 135), C(24, 46, 58), 90f))
        {
            g.FillRectangle(b, glass);
        }
        using (Pen p = new Pen(A(C(255, 220, 170), 50), 2))
        {
            g.DrawLine(p, r.X + r.Width - 18, r.Y + 20, r.X + r.Width - 18, r.Bottom - 20);
        }
        using (SolidBrush knob = new SolidBrush(C(176, 126, 62)))
        {
            g.FillEllipse(knob, r.X + 12, r.Y + r.Height / 2, 8, 8);
        }
    }

    static void DrawCounter(Graphics g, RectangleF r, double t)
    {
        using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(r.X, r.Y, r.Width, 50), C(126, 82, 48), C(72, 44, 28), 90f))
        {
            g.FillRectangle(b, r.X, r.Y, r.Width, 50);
        }
        using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(r.X, r.Y + 50, r.Width, r.Height - 50), C(60, 36, 22), C(26, 16, 11), 90f))
        {
            g.FillRectangle(b, r.X, r.Y + 50, r.Width, r.Height - 50);
        }
        using (Pen p = new Pen(A(C(255, 220, 170), 60), 2))
        {
            g.DrawLine(p, r.X, r.Y, r.Right, r.Y);
        }
        using (Pen p = new Pen(A(C(20, 12, 8), 120), 2))
        {
            for (int i = 0; i < 12; i++) g.DrawLine(p, r.X + 30 + i * 85, r.Y + 60, r.X + 30 + i * 85, r.Bottom);
        }
        using (Pen p = new Pen(C(176, 126, 62), 3))
        {
            g.DrawLine(p, r.X + 40, r.Bottom - 38, r.Right - 40, r.Bottom - 38);
        }
    }

    static void DrawEspressoMachine(Graphics g, float cx, float cy, double t)
    {
        RectangleF body = new RectangleF(cx - 110, cy - 70, 220, 140);
        using (SolidBrush b = new SolidBrush(C(30, 61, 55)))
        {
            FillRound(g, b, body, 14);
        }
        using (SolidBrush brass = new SolidBrush(C(176, 126, 62)))
        {
            FillRound(g, brass, new RectangleF(cx - 90, cy - 52, 180, 22), 6);
            g.FillEllipse(brass, cx - 34, cy - 20, 68, 34);
        }
        using (SolidBrush dark = new SolidBrush(C(23, 25, 24)))
        {
            FillRound(g, dark, new RectangleF(cx - 26, cy + 6, 52, 24), 5);
        }
        using (Pen handle = new Pen(C(60, 40, 26), 7))
        {
            handle.EndCap = LineCap.Round;
            g.DrawLine(handle, cx + 22, cy + 18, cx + 58, cy + 30);
        }
        using (SolidBrush cup = new SolidBrush(C(246, 231, 206)))
        {
            g.FillEllipse(cup, cx - 20, cy + 30, 40, 14);
            g.FillRectangle(cup, cx - 16, cy + 33, 32, 16);
        }
        DrawSteam(g, cx, cy - 70, t, 3, 60);
    }

    static void DrawLamp(Graphics g, float x, float y, float r, double t)
    {
        using (Pen cord = new Pen(C(24, 18, 14), 4))
        {
            g.DrawLine(cord, x, 0, x, y);
        }
        using (SolidBrush glow = new SolidBrush(A(C(255, 224, 170), 14)))
        {
            g.FillEllipse(glow, x - 34, y + 22, 68, 30);
        }
        using (GraphicsPath shade = new GraphicsPath())
        {
            shade.AddPolygon(new PointF[]
            {
                new PointF(x - r * 0.55f, y),
                new PointF(x + r * 0.55f, y),
                new PointF(x + r * 0.34f, y + 30),
                new PointF(x - r * 0.34f, y + 30)
            });
            using (SolidBrush b = new SolidBrush(C(54, 36, 24)))
            {
                g.FillPath(b, shade);
            }
        }
        using (SolidBrush bulb = new SolidBrush(C(255, 224, 170)))
        {
            g.FillEllipse(bulb, x - 10, y + 28, 20, 12);
        }
    }

    static void DrawClock(Graphics g, float cx, float cy, float r)
    {
        using (SolidBrush face = new SolidBrush(C(246, 231, 206)))
        {
            g.FillEllipse(face, cx - r, cy - r, r * 2, r * 2);
        }
        using (Pen rim = new Pen(C(54, 36, 24), 4))
        {
            g.DrawEllipse(rim, cx - r, cy - r, r * 2, r * 2);
        }
        using (Pen tick = new Pen(C(54, 36, 24), 2))
        {
            for (int i = 0; i < 12; i++)
            {
                double a = i * Math.PI / 6.0;
                g.DrawLine(tick, cx + (float)(Math.Cos(a) * r * 0.75), cy + (float)(Math.Sin(a) * r * 0.75), cx + (float)(Math.Cos(a) * r * 0.88), cy + (float)(Math.Sin(a) * r * 0.88));
            }
        }
        double ha = (6.0 + 35.0 / 60.0) / 12.0 * Math.PI * 2.0 - Math.PI / 2.0;
        double ma = 35.0 / 60.0 * Math.PI * 2.0 - Math.PI / 2.0;
        using (Pen hand = new Pen(C(54, 36, 24), 4))
        {
            g.DrawLine(hand, cx, cy, cx + (float)(Math.Cos(ha) * r * 0.45), cy + (float)(Math.Sin(ha) * r * 0.45));
            g.DrawLine(hand, cx, cy, cx + (float)(Math.Cos(ma) * r * 0.68), cy + (float)(Math.Sin(ma) * r * 0.68));
        }
        using (SolidBrush dot = new SolidBrush(C(214, 90, 74)))
        {
            g.FillEllipse(dot, cx - 4, cy - 4, 8, 8);
        }
    }

    static void DrawDust(Graphics g, double t)
    {
        for (int i = 0; i < 30; i++)
        {
            double x = (i * 137.5 + Math.Sin(t * 0.2 + i) * 20.0) % W;
            double y = (i * 71.3 + Math.Cos(t * 0.17 + i * 1.7) * 16.0) % H;
            int a = 12 + (i % 5) * 3;
            using (SolidBrush b = new SolidBrush(A(C(255, 224, 170), a)))
            {
                g.FillEllipse(b, (float)x, (float)y, 2.0f + (i % 3), 2.0f + (i % 3));
            }
        }
    }

    // ---------- Character ----------

    static void DrawXiaoman(Graphics g, float x, float y, float s, string pose, double local)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.ScaleTransform(s, s);

        // shadow
        using (SolidBrush sh = new SolidBrush(A(C(0, 0, 0), 70)))
        {
            g.FillEllipse(sh, -70, -14, 140, 24);
        }

        // trousers (mostly hidden)
        using (SolidBrush trouser = new SolidBrush(C(35, 38, 42)))
        {
            FillRound(g, trouser, new RectangleF(-38, -120, 76, 118), 14);
        }

        // shirt
        using (SolidBrush shirt = new SolidBrush(C(243, 228, 202)))
        {
            FillRound(g, shirt, new RectangleF(-58, -252, 116, 172), 28);
        }

        // apron
        using (SolidBrush apron = new SolidBrush(C(176, 74, 62)))
        {
            FillRound(g, apron, new RectangleF(-46, -225, 92, 145), 12);
        }
        using (Pen strap = new Pen(C(176, 74, 62), 8))
        {
            g.DrawLine(strap, -32, -250, -26, -220);
            g.DrawLine(strap, 32, -250, 26, -220);
        }

        // neck
        using (SolidBrush skin = new SolidBrush(C(232, 190, 155)))
        {
            FillRound(g, skin, new RectangleF(-13, -274, 26, 34), 8);
        }

        // hair back
        using (SolidBrush hair = new SolidBrush(C(28, 26, 27)))
        {
            g.FillEllipse(hair, -54, -366, 108, 100);
            g.FillEllipse(hair, -56, -335, 22, 82);
            g.FillEllipse(hair, 34, -335, 22, 82);
        }

        // face
        using (SolidBrush skin = new SolidBrush(C(238, 198, 163)))
        {
            g.FillEllipse(skin, -43, -352, 86, 92);
        }
        // fringe
        using (SolidBrush hair = new SolidBrush(C(28, 26, 27)))
        {
            GraphicsPath fringe = new GraphicsPath();
            fringe.AddBezier(-46, -340, -38, -370, 20, -378, 44, -342);
            fringe.AddBezier(44, -342, 22, -330, -18, -326, -46, -340);
            fringe.CloseFigure();
            g.FillPath(hair, fringe);
        }

        // ears + earring
        using (SolidBrush skin = new SolidBrush(C(232, 190, 155)))
        {
            g.FillEllipse(skin, -50, -316, 14, 22);
            g.FillEllipse(skin, 36, -316, 14, 22);
        }
        using (SolidBrush silver = new SolidBrush(C(210, 216, 218)))
        {
            g.FillEllipse(silver, -50, -304, 5, 5);
        }

        // eyes
        bool blink = (local > 0.45 && local < 0.50) || (local > 0.78 && local < 0.82);
        using (Pen eye = new Pen(C(42, 33, 30), 2.2f))
        {
            if (blink)
            {
                g.DrawLine(eye, -26, -314, -12, -314);
                g.DrawLine(eye, 12, -314, 26, -314);
            }
            else
            {
                g.DrawArc(eye, -28, -320, 16, 12, 200, 140);
                g.DrawArc(eye, 12, -320, 16, 12, 200, 140);
            }
        }
        using (SolidBrush pupil = new SolidBrush(C(34, 28, 26)))
        {
            if (!blink)
            {
                g.FillEllipse(pupil, -22, -316, 5, 5);
                g.FillEllipse(pupil, 18, -316, 5, 5);
            }
        }
        // brows
        using (Pen brow = new Pen(C(40, 31, 28), 2))
        {
            g.DrawLine(brow, -28, -330, -13, -332);
            g.DrawLine(brow, 13, -332, 28, -330);
        }
        // nose + mouth
        using (Pen nose = new Pen(A(C(180, 125, 98), 150), 1.5f))
        {
            g.DrawLine(nose, 0, -310, -2, -300);
        }
        using (Pen mouth = new Pen(C(150, 72, 66), 2))
        {
            g.DrawArc(mouth, -10, -294, 20, 8, 10, 160);
        }
        // name tag
        using (SolidBrush tag = new SolidBrush(C(246, 231, 206)))
        {
            FillRound(g, tag, new RectangleF(12, -222, 34, 18), 3);
        }
        using (Font f = new Font(uiFont, 9.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(C(54, 36, 24)))
        {
            g.DrawString("小满", f, b, 15, -221);
        }

        // arms + hands
        using (Pen arm = new Pen(C(238, 198, 163), 16))
        {
            arm.StartCap = LineCap.Round;
            arm.EndCap = LineCap.Round;
            if (pose == "wait")
            {
                g.DrawLine(arm, -50, -235, -32, -160);
                g.DrawLine(arm, 50, -235, 32, -160);
            }
            else if (pose == "write")
            {
                g.DrawLine(arm, -50, -235, -38, -150);
                g.DrawLine(arm, 50, -235, 78, -150);
            }
            else if (pose == "lift")
            {
                g.DrawLine(arm, -50, -235, -66, -150);
                g.DrawLine(arm, 50, -235, 72, -252);
            }
            else
            {
                g.DrawLine(arm, -50, -235, -70, -145);
                g.DrawLine(arm, 50, -235, 70, -145);
            }
        }

        if (pose == "wait")
        {
            DrawCup(g, -36, -150, 0.62f, "", 0);
            DrawCup(g, 36, -150, 0.62f, "", 0);
        }
        else if (pose == "lift")
        {
            DrawCup(g, 78, -258, 0.62f, "", 0);
        }
        else
        {
            DrawCup(g, 72, -140, 0.62f, "", 0);
        }

        // rim light
        using (Pen rim = new Pen(A(C(255, 210, 150), 80), 3))
        {
            g.DrawArc(rim, -46, -354, 92, 96, -70, 80);
        }

        g.Restore(st);
    }

    static void DrawHand(Graphics g, float x, float y, float s, float angle)
    {
        GraphicsState st = g.Save();
        g.TranslateTransform(x, y);
        g.RotateTransform(angle);
        g.ScaleTransform(s, s);
        using (SolidBrush skin = new SolidBrush(C(238, 198, 163)))
        {
            g.FillEllipse(skin, -42, -20, 84, 48);
            g.FillEllipse(skin, -30, -34, 22, 30);
            g.FillEllipse(skin, -8, -38, 22, 32);
            g.FillEllipse(skin, 14, -34, 22, 30);
        }
        using (Pen line = new Pen(A(C(180, 125, 98), 90), 1.5f))
        {
            g.DrawArc(line, -30, -8, 24, 20, 20, 120);
            g.DrawArc(line, 2, -8, 24, 20, 20, 120);
        }
        g.Restore(st);
    }

    // ---------- Props ----------

    static void DrawCup(Graphics g, float x, float y, float s, string sleeveText, double t)
    {
        // saucer
        using (SolidBrush saucer = new SolidBrush(A(C(238, 222, 196), 90)))
        {
            g.FillEllipse(saucer, x - 52 * s, y + 20 * s, 104 * s, 26 * s);
        }
        // body
        using (GraphicsPath cup = new GraphicsPath())
        {
            cup.AddBezier(x - 32 * s, y - 45 * s, x - 38 * s, y + 10 * s, x - 22 * s, y + 42 * s, x, y + 42 * s);
            cup.AddBezier(x, y + 42 * s, x + 22 * s, y + 42 * s, x + 38 * s, y + 10 * s, x + 32 * s, y - 45 * s);
            cup.CloseFigure();
            using (LinearGradientBrush b = new LinearGradientBrush(new RectangleF(x - 34 * s, y - 46 * s, 68 * s, 90 * s), C(255, 244, 220), C(206, 184, 150), 0f))
            {
                g.FillPath(b, cup);
            }
        }
        // handle
        using (Pen handle = new Pen(C(230, 210, 180), 6 * s))
        {
            g.DrawArc(handle, x + 24 * s, y - 28 * s, 26 * s, 36 * s, -90, 180);
        }
        // rim
        using (Pen rim = new Pen(C(255, 248, 230), 2.5f * s))
        {
            g.DrawArc(rim, x - 31 * s, y - 48 * s, 62 * s, 12 * s, 180, 180);
        }
        // sleeve
        if (sleeveText != null)
        {
            RectangleF sleeve = new RectangleF(x - 34 * s, y - 16 * s, 68 * s, 34 * s);
            using (SolidBrush b = new SolidBrush(C(186, 141, 91)))
            {
                FillRound(g, b, sleeve, 4 * s);
            }
            if (sleeveText != null && sleeveText.Length > 0)
            {
                using (Font f = new Font(handFont, 10.0f * s, FontStyle.Regular, GraphicsUnit.Pixel))
                using (SolidBrush b = new SolidBrush(C(30, 22, 18)))
                {
                    using (StringFormat sf = new StringFormat())
                    {
                        sf.Alignment = StringAlignment.Center;
                        sf.LineAlignment = StringAlignment.Center;
                        g.DrawString(sleeveText, f, b, sleeve, sf);
                    }
                }
            }
        }
        if (t > 0) DrawSteam(g, x, y - 50 * s, t, 2, 55 * s);
    }

    static void DrawForegroundCup(Graphics g, float x, float y, float s, double t)
    {
        DrawCup(g, x, y, s, "", t);
        using (SolidBrush b = new SolidBrush(A(C(255, 220, 170), 20)))
        {
            g.FillEllipse(b, x - 60 * s, y + 20 * s, 120 * s, 30 * s);
        }
    }

    static void DrawSteam(Graphics g, float x, float y, double t, int count, float height)
    {
        using (Pen p = new Pen(A(C(255, 255, 255), 34), 2.0f))
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

    static void DrawReflections(Graphics g, double t)
    {
        using (SolidBrush warm = new SolidBrush(A(C(242, 181, 107), 26)))
        {
            g.FillRectangle(warm, 800, 570, 120, 130);
            g.FillRectangle(warm, 930, 575, 70, 120);
            g.FillRectangle(warm, 1010, 580, 50, 100);
        }
        using (SolidBrush cool = new SolidBrush(A(C(120, 180, 210), 18)))
        {
            g.FillRectangle(cool, 180, 570, 60, 130);
        }
        using (Pen p = new Pen(A(C(255, 220, 170), 16), 2))
        {
            for (int i = 0; i < 8; i++)
            {
                float x = 780 + i * 50;
                g.DrawLine(p, x, 580, x + (float)Math.Sin(t + i) * 6, 700);
            }
        }
    }

    static void DrawTitleMark(Graphics g, string text, float x, float y)
    {
        using (Font f = new Font(uiFont, 16.0f, FontStyle.Regular, GraphicsUnit.Pixel))
        using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 130)))
        {
            g.DrawString(text, f, b, x, y);
        }
    }

    // ---------- Global post ----------

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
        RenderStill(Path.Combine(assetsDir, "characters", "xiaoman_sheet.png"), 1600, 900, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, 1600, 900), C(14, 42, 44), C(35, 27, 21), 90);
            using (Font f = new Font(uiFont, 36.0f, FontStyle.Bold, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(C(246, 231, 206)))
            {
                g.DrawString("小满 / 角色定妆照", f, b, 70, 50);
            }
            using (Font f = new Font(uiFont, 18.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 180)))
            {
                g.DrawString("短发 · 银色耳钉 · 奶油衬衫 · 砖红围裙", f, b, 74, 104);
            }
            DrawXiaoman(g, 360, 760, 1.45f, "counter", 0.1);
            DrawXiaoman(g, 800, 760, 1.45f, "wait", 0.1);
            DrawXiaoman(g, 1240, 760, 1.45f, "lift", 0.1);
            using (Font f = new Font(uiFont, 16.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush b = new SolidBrush(A(C(246, 231, 206), 160)))
            {
                g.DrawString("柜台 / 等待 / 递出", f, b, 300, 830);
                g.DrawString("柜台 / 等待 / 递出", f, b, 740, 830);
                g.DrawString("柜台 / 等待 / 递出", f, b, 1180, 830);
            }
        });

        RenderStill(Path.Combine(assetsDir, "scenes", "cafe_dawn.png"), W, H, delegate(Graphics g)
        {
            DrawCafeBase(g, 0, false, "counter", 0);
        });

        RenderStill(Path.Combine(assetsDir, "scenes", "street_rain.png"), W, H, delegate(Graphics g)
        {
            DrawStreetScene(g, 0, 0, false, 900, 0.92f, "wait", 0);
        });

        RenderStill(Path.Combine(assetsDir, "props", "cup_sleeve.png"), 1000, 700, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, 1000, 700), C(44, 27, 18), C(10, 9, 8), 90);
            DrawCup(g, 500, 430, 2.6f, "给晚到的人", 0);
            DrawWarmRim(g, 330, 250, 340, 360, 0.12);
        });

        RenderStill(Path.Combine(outputDir, "cover.png"), W, H, delegate(Graphics g)
        {
            Grad(g, new RectangleF(0, 0, W, H), C(8, 24, 26), C(48, 28, 19), 90);
            DrawRadialGlow(g, new RectangleF(360, 70, 560, 560), C(255, 190, 100), 34);
            using (Font title = new Font(uiFont, 66.0f, FontStyle.Bold, GraphicsUnit.Pixel))
            using (Font sub = new Font(uiFont, 28.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (Font small = new Font(uiFont, 14.0f, FontStyle.Regular, GraphicsUnit.Pixel))
            using (SolidBrush white = new SolidBrush(C(246, 231, 206)))
            using (SolidBrush amber = new SolidBrush(C(242, 181, 107)))
            {
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString("晚到也算到", title, white, new RectangleF(0, 240, W, 100), sf);
                    g.DrawString("街角咖啡馆 · 24 秒本地 Demo", sub, amber, new RectangleF(0, 360, W, 60), sf);
                    g.DrawString("LOCAL ANIMATIC / 2026", small, new SolidBrush(A(C(246, 231, 206), 140)), new RectangleF(0, 640, W, 30), sf);
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
