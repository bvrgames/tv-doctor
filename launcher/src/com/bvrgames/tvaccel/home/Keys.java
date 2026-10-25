package com.bvrgames.tvaccel.home;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

// Remote keys that open an app the TV no longer has: Netflix and Prime Video.
// The Prime target is saved by tvaccel at install time (--es prime <package>|ask|keep).
final class Keys {
    static final String PREFS = "config";
    static final String PRIME_PREF = "prime";
    static final String ASK = "ask", KEEP = "keep";
    static final String PRIME_VIDEO = "com.amazon.amazonvideo.livingroom";
    static final String NETFLIX = "com.netflix.ninja";
    static final String YOUTUBE = "com.google.android.youtube.tv";
    // SmartTube, only if the person installed it themselves: stable, beta, old package name.
    static final String[] SMARTTUBE = {"com.teamsmart.videomanager.tv", "com.liskovsoft.smarttubetv.beta",
            "com.liskovsoft.smarttubetv"};

    private Keys() {}

    static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREFS, 0);
    }

    // True if the package is installed and switched on.
    static boolean enabled(Context c, String pkg) {
        try { return c.getPackageManager().getApplicationInfo(pkg, 0).enabled; }
        catch (PackageManager.NameNotFoundException e) { return false; }
    }

    static boolean launch(Context c, String pkg) {
        PackageManager pm = c.getPackageManager();
        Intent i = pm.getLeanbackLaunchIntentForPackage(pkg);
        if (i == null) i = pm.getLaunchIntentForPackage(pkg);
        if (i == null) return false;
        try {
            c.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    // The menu takes the Netflix key's nflx:// link only while Netflix itself can't (off or missing);
    // otherwise both would answer and Android would ask which one every time.
    static void syncNetflixKey(Context c) {
        android.content.ComponentName handler = new android.content.ComponentName(c, NetflixKeyActivity.class);
        int want = enabled(c, NETFLIX) ? PackageManager.COMPONENT_ENABLED_STATE_DISABLED
                : PackageManager.COMPONENT_ENABLED_STATE_ENABLED;
        PackageManager pm = c.getPackageManager();
        if (pm.getComponentEnabledSetting(handler) != want)
            pm.setComponentEnabledSetting(handler, want, PackageManager.DONT_KILL_APP);
    }

    // The Netflix key: SmartTube if the person installed it, else YouTube.
    static void openVideo(Context c) {
        for (String p : SMARTTUBE) if (enabled(c, p) && launch(c, p)) return;
        launch(c, YOUTUBE);
    }
}
