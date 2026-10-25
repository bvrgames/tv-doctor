package com.bvrgames.tvaccel.home;

import android.app.Activity;
import android.os.Bundle;

// Receives the nflx:// link the Netflix key sends, while Netflix itself is off (see the manifest).
public class NetflixKeyActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Keys.openVideo(this);
        finish();
    }
}
