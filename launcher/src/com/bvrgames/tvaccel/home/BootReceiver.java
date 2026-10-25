package com.bvrgames.tvaccel.home;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

// Starts the Prime key watcher after a restart (the home screen may not start before a key press).
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        Keys.syncNetflixKey(c);
        KeyWatchService.startIfNeeded(c);
    }
}
