package com.bvrgames.tvaccel.home;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import java.io.BufferedReader;
import java.io.InputStreamReader;

// The Prime Video key on Xiaomi sticks is handled by the system before any app sees it: it starts
// Prime Video's activity by name, so nothing can catch the key. When Prime Video is off, that start
// still shows up in the system log, and this service opens the chosen app instead.
// Needs READ_LOGS, which tvaccel grants over adb (Android 9-12; 13+ asks the user each time).
public class KeyWatchService extends Service {
    private static final String CHANNEL = "keys";
    private static final String MARK = "cmp=" + Keys.PRIME_VIDEO + "/";
    private final Handler main = new Handler(Looper.getMainLooper());
    private volatile boolean running;
    private Process logcat;

    static void startIfNeeded(Context c) {
        String target = Keys.prefs(c).getString(Keys.PRIME_PREF, null);
        if (target == null || Keys.KEEP.equals(target)) return;
        if (c.getPackageManager().checkPermission(android.Manifest.permission.READ_LOGS, c.getPackageName())
                != PackageManager.PERMISSION_GRANTED) return;
        Intent i = new Intent(c, KeyWatchService.class);
        try {
            if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i);
            else c.startService(i);
        } catch (Exception ignored) {}
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Notification n;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            nm.createNotificationChannel(new NotificationChannel(CHANNEL, "Remote keys", NotificationManager.IMPORTANCE_MIN));
            n = new Notification.Builder(this, CHANNEL).setSmallIcon(android.R.drawable.ic_media_play)
                    .setContentTitle("Remote keys").build();
        } else {
            n = new Notification.Builder(this).setSmallIcon(android.R.drawable.ic_media_play)
                    .setContentTitle("Remote keys").build();
        }
        if (Build.VERSION.SDK_INT >= 34) startForeground(1, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        else startForeground(1, n);
        if (!running) {
            running = true;
            new Thread(this::watch, "prime-key").start();
        }
        return START_STICKY;
    }

    // Follows ActivityManager lines from now on (-T <now>: older lines could be an earlier Prime
    // press), so it sleeps until something starts.
    private void watch() {
        while (running) {
            try {
                String now = new java.text.SimpleDateFormat("MM-dd HH:mm:ss.SSS", java.util.Locale.US)
                        .format(new java.util.Date());
                logcat = Runtime.getRuntime().exec(new String[] {"logcat", "-v", "brief", "-T", now,
                        "ActivityManager:I", "ActivityTaskManager:I", "*:S"});
                BufferedReader r = new BufferedReader(new InputStreamReader(logcat.getInputStream()));
                String line;
                while (running && (line = r.readLine()) != null) {
                    if (line.contains("START u0") && line.contains(MARK)) main.post(this::onPrime);
                }
            } catch (Exception ignored) {}
            if (running) try { Thread.sleep(5000); } catch (InterruptedException e) { return; }
        }
    }

    private void onPrime() {
        if (Keys.enabled(this, Keys.PRIME_VIDEO)) return; // Prime Video works: leave its key alone
        String target = Keys.prefs(this).getString(Keys.PRIME_PREF, Keys.KEEP);
        if (Keys.KEEP.equals(target)) return;
        if (Keys.ASK.equals(target)) {
            startActivity(new Intent(this, MainActivity.class).putExtra("choosePrime", true)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            return;
        }
        Keys.launch(this, target);
    }

    @Override
    public void onDestroy() {
        running = false;
        if (logcat != null) logcat.destroy();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
