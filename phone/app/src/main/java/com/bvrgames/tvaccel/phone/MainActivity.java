package com.bvrgames.tvaccel.phone;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

// The phone version of the program: the same Python window as on Windows and Mac, served by the
// app on 127.0.0.1 and shown in a WebView. adb goes through AdbBridge (libadb-android).
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        TextView loading = new TextView(this);
        loading.setText("TV Doctor…");
        loading.setTextColor(Color.WHITE);
        loading.setGravity(Gravity.CENTER);
        loading.setBackgroundColor(0xFF07070A);
        setContentView(loading);

        AdbBridge.init(this);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
        new Thread(() -> {
            PyObject served = Python.getInstance().getModule("tvaccel.gui").callAttr("serve", 0);
            String url = served.asList().get(1).toString();
            runOnUiThread(() -> show(url));
        }).start();
    }

    private void show(String url) {
        web = new WebView(this);
        web.setBackgroundColor(0xFF07070A);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setSupportMultipleWindows(false);  // "Open the report" opens in place; Back returns
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());  // confirm() for "Undo"
        setContentView(web);
        web.loadUrl(url);
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
}
