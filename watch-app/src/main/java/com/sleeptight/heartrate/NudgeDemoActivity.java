package com.sleeptight.heartrate;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Presentation-only Wear OS concept for Codex-directed bedtime nudges.
 * It is entirely local: no receiver, phone, account, or live Codex connection is required.
 */
public final class NudgeDemoActivity extends Activity {
    private static final String[][] NUDGES = {
            {"Breathe and settle", "One quiet minute before the lights fade."},
            {"A gentle hello", "Your wind-down window is coming up."},
            {"Time to wind down", "Your usual calm window starts now."},
            {"Feeling sleepy?", "Keep tonight simple and dim."},
            {"Release the day", "A small stretch, then screens away."},
            {"Routine complete", "Nice work. The rest of tonight stays quiet."},
            {"Sleep well", "Nudges are now paused until morning."},
            {"Good morning", "How did that routine feel?"}
    };

    private NudgeSpriteView mascot;
    private TextView title;
    private TextView body;
    private TextView mode;
    private int frame = 2;
    private int profileMode = 1;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(24), dp(14), dp(24), dp(28));
        root.setBackgroundColor(0xFF090B11);

        mode = label("CODEX ADAPTING", 10, 0xFFFF9B6A);
        mascot = new NudgeSpriteView();
        mascot.setLayoutParams(new LinearLayout.LayoutParams(dp(126), dp(126)));
        title = label("Time to wind down", 19, Color.WHITE);
        title.setGravity(Gravity.CENTER);
        body = label("Your usual calm window starts now.", 11, 0xFFB8B3AD);
        body.setGravity(Gravity.CENTER);

        LinearLayout actions = new LinearLayout(this);
        actions.setGravity(Gravity.CENTER);
        Button next = button("Next nudge", true);
        Button profile = button("Change mode", false);
        actions.addView(next);
        actions.addView(space(8));
        actions.addView(profile);

        root.addView(mode);
        root.addView(mascot);
        root.addView(title, matchWrap());
        root.addView(space(5));
        root.addView(body, matchWrap());
        root.addView(space(12));
        root.addView(actions);
        setContentView(root);

        next.setOnClickListener(v -> {
            frame = (frame + 1) % NUDGES.length;
            renderNudge(true);
        });
        profile.setOnClickListener(v -> {
            profileMode = (profileMode + 1) % 3;
            String[] labels = {"FIXED PROFILE", "CODEX ADAPTING", "CODEX PAUSED"};
            mode.setText(labels[profileMode]);
            body.setText(profileMode == 0
                    ? "Your proven routine continues without new changes."
                    : profileMode == 1
                    ? NUDGES[frame][1]
                    : "Learning is off. Your current routine still works.");
        });
        renderNudge(false);
    }

    private void renderNudge(boolean vibrate) {
        mascot.setFrame(frame);
        title.setText(NUDGES[frame][0]);
        body.setText(NUDGES[frame][1]);
        if (vibrate) {
            Vibrator vibrator = getSystemService(Vibrator.class);
            if (vibrator != null && vibrator.hasVibrator()) {
                vibrator.vibrate(VibrationEffect.createWaveform(new long[]{0, 55, 70, 55}, -1));
            }
        }
    }

    private TextView label(String value, int sp, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        return view;
    }

    private Button button(String value, boolean primary) {
        Button view = new Button(this);
        view.setText(value);
        view.setTextSize(10);
        view.setMinHeight(dp(42));
        view.setTextColor(primary ? 0xFF32160B : Color.WHITE);
        view.setBackgroundColor(primary ? 0xFFFF9B6A : 0xFF252A35);
        return view;
    }

    private View space(int width) {
        View view = new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(dp(width), dp(width)));
        return view;
    }

    private ViewGroup.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private final class NudgeSpriteView extends View {
        private final Bitmap sheet = BitmapFactory.decodeResource(getResources(), R.drawable.mimo_sprite_sheet);
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        private int selectedFrame = 2;

        NudgeSpriteView() { super(NudgeDemoActivity.this); }

        void setFrame(int value) {
            selectedFrame = Math.max(0, Math.min(7, value));
            animate().cancel();
            setScaleX(.88f);
            setScaleY(.88f);
            animate().scaleX(1f).scaleY(1f).setDuration(220).start();
            invalidate();
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            int cellWidth = sheet.getWidth() / 4;
            int cellHeight = sheet.getHeight() / 2;
            int column = selectedFrame % 4;
            int row = selectedFrame / 4;
            Rect source = new Rect(column * cellWidth, row * cellHeight,
                    (column + 1) * cellWidth, (row + 1) * cellHeight);
            Rect destination = new Rect(0, 0, getWidth(), getHeight());
            canvas.drawBitmap(sheet, source, destination, paint);
        }
    }
}
