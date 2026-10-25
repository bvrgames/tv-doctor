package com.bvrgames.tvaccel.home;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.BitmapDrawable;
import android.os.Handler;
import android.os.Looper;
import android.service.dreams.DreamService;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextClock;

import java.util.Random;

// Screensaver in the menu's style: a large thin clock and the date in the middle, over the menu's
// soft glow slowly shifting colour. Against burn-in the clock drifts a little around the centre every
// minute and the screen is dimmed; tvaccel also puts the TV to sleep a few minutes later.
public class ClockDream extends DreamService {
    private static final long DRIFT_EVERY_MS = 60_000;
    private static final long COLOUR_EVERY_MS = 30_000; // four colours: one cycle in about two minutes
    private static final int FADE_MS = 8_000;
    private static final int[][] GLOWS = { // main glow, second glow
        {0xFF9A3CC8, 0xFF1E6EBE}, // violet, blue
        {0xFF2F6BE0, 0xFF19A3A0}, // blue, teal
        {0xFF14A8A0, 0xFF6A3CC8}, // teal, violet
        {0xFFC83C78, 0xFF2F5BD0}, // raspberry, blue
    };
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Random random = new Random();
    private ImageView[] layers;
    private int front, colour;
    private LinearLayout clock;
    private float scale;

    @Override
    public void onAttachedToWindow() {
        super.onAttachedToWindow();
        setInteractive(false);
        setFullscreen(true);
        setScreenBright(false);

        scale = getResources().getDisplayMetrics().widthPixels / 1920f;
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF050407);
        layers = new ImageView[] {new ImageView(this), new ImageView(this)};
        for (ImageView v : layers) {
            v.setScaleType(ImageView.ScaleType.FIT_XY);
            root.addView(v, new FrameLayout.LayoutParams(-1, -1));
        }
        layers[0].setImageDrawable(glow(GLOWS[0]));
        layers[1].setAlpha(0f);

        clock = new LinearLayout(this);
        clock.setOrientation(LinearLayout.VERTICAL);
        clock.setGravity(Gravity.CENTER_HORIZONTAL);
        TextClock time = text("H:mm", "h:mm", 250, 0xEBFFFFFF, Typeface.create("sans-serif-thin", Typeface.NORMAL));
        time.setLetterSpacing(-0.02f);
        time.setIncludeFontPadding(false);
        // Full width, centred text: wrap_content measured the thin digits too narrow and cut the last one.
        clock.addView(time, new LinearLayout.LayoutParams(-1, -2));
        String day = Strings.datePattern();
        TextClock date = text(day, day, 44, 0x99FFFFFF, Typeface.create("sans-serif-light", Typeface.NORMAL));
        LinearLayout.LayoutParams dp = new LinearLayout.LayoutParams(-2, -2);
        dp.topMargin = px(18);
        clock.addView(date, dp);
        root.addView(clock, new FrameLayout.LayoutParams(-1, -2, Gravity.CENTER));
        setContentView(root);

        handler.postDelayed(this::drift, DRIFT_EVERY_MS);
        handler.postDelayed(this::nextColour, COLOUR_EVERY_MS);
    }

    private int px(int v) {
        return Math.round(v * scale);
    }

    private TextClock text(String f24, String f12, int size, int color, Typeface tf) {
        TextClock t = new TextClock(this);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        t.setFormat24Hour(f24);
        t.setFormat12Hour(f12);
        t.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(size));
        t.setTextColor(color);
        t.setTypeface(tf);
        t.setFontFeatureSettings("tnum");
        return t;
    }

    // A small step to a random spot around the centre (at most ~70 px at 1080p), slid, not jumped.
    private void drift() {
        int r = px(70);
        clock.animate().translationX(random.nextInt(2 * r + 1) - r).translationY(random.nextInt(2 * r + 1) - r)
                .setDuration(2_000).start();
        handler.postDelayed(this::drift, DRIFT_EVERY_MS);
    }

    // Cross-fades the back layer, painted with the next colours, over the front one.
    private void nextColour() {
        colour = (colour + 1) % GLOWS.length;
        final ImageView back = layers[1 - front], top = layers[front];
        back.setImageDrawable(glow(GLOWS[colour]));
        back.setAlpha(0f);
        back.bringToFront();
        clock.bringToFront();
        back.animate().alpha(1f).setDuration(FADE_MS).withLayer()
                .withEndAction(() -> top.setImageDrawable(null)).start();
        front = 1 - front;
        handler.postDelayed(this::nextColour, COLOUR_EVERY_MS);
    }

    // Same trick as the menu's shelf: drawn small and stretched, so it is soft and cheap.
    private BitmapDrawable glow(int[] c) {
        int w = 240, h = 135;
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        int a = c[0] & 0xFFFFFF, s = c[1] & 0xFFFFFF;
        p.setShader(new RadialGradient(w * 0.36f, h * 0.40f, w * 0.55f,
                new int[] {0x8C000000 | a, 0x38000000 | a, a}, new float[] {0f, 0.5f, 1f}, Shader.TileMode.CLAMP));
        cv.drawRect(0, 0, w, h, p);
        p.setShader(new RadialGradient(w * 0.80f, h * 0.78f, w * 0.45f,
                new int[] {0x60000000 | s, s}, null, Shader.TileMode.CLAMP));
        cv.drawRect(0, 0, w, h, p);
        BitmapDrawable d = new BitmapDrawable(getResources(), b);
        d.setFilterBitmap(true);
        d.setDither(true);
        return d;
    }

    @Override
    public void onDetachedFromWindow() {
        handler.removeCallbacksAndMessages(null);
        super.onDetachedFromWindow();
    }
}
