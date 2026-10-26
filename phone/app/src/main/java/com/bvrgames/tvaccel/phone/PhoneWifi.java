package com.bvrgames.tvaccel.phone;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.provider.Settings;

import java.util.TreeSet;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

// The Wi-Fi networks the phone sees, for the 5 GHz region check (tvaccel/wifi.py): what
// system_profiler / netsh / nmcli give on a computer. Android shows scan results only with the
// location permission and with location turned on.
public final class PhoneWifi {
    static final int ASK_LOCATION = 1;
    private static Activity activity;
    private static CountDownLatch answered;

    private PhoneWifi() {}

    static void init(Activity a) { activity = a; }

    static void onPermissionAnswer() {
        if (answered != null) answered.countDown();
    }

    // 5 GHz channels the phone sees, space-separated ("" if none); null if it cannot scan.
    public static String fiveGhzChannels() throws Exception {
        Context c = activity.getApplicationContext();
        if (!allowed(c)) {
            answered = new CountDownLatch(1);
            activity.runOnUiThread(() -> activity.requestPermissions(
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, ASK_LOCATION));
            answered.await(60, TimeUnit.SECONDS);
            if (!allowed(c)) return null;
        }
        if (!locationOn(c)) return null;

        WifiManager wm = c.getSystemService(WifiManager.class);
        if (!wm.isWifiEnabled()) return null;
        CountDownLatch scanned = new CountDownLatch(1);
        BroadcastReceiver done = new BroadcastReceiver() {
            @Override public void onReceive(Context x, Intent i) { scanned.countDown(); }
        };
        c.registerReceiver(done, new IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION));
        try {
            if (wm.startScan()) scanned.await(10, TimeUnit.SECONDS);  // refused (too often): last results
        } finally {
            c.unregisterReceiver(done);
        }
        TreeSet<Integer> channels = new TreeSet<>();
        for (ScanResult r : wm.getScanResults()) {
            if (r.frequency >= 5000 && r.frequency <= 5900) channels.add((r.frequency - 5000) / 5);
        }
        StringBuilder out = new StringBuilder();
        for (int ch : channels) out.append(ch).append(' ');
        return out.toString().trim();
    }

    private static boolean allowed(Context c) {
        return c.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private static boolean locationOn(Context c) {
        if (Build.VERSION.SDK_INT >= 28) return c.getSystemService(LocationManager.class).isLocationEnabled();
        return Settings.Secure.getInt(c.getContentResolver(), Settings.Secure.LOCATION_MODE, 0) != 0;
    }
}
