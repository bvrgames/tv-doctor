package com.bvrgames.tvaccel.phone;

import android.content.Context;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

import io.github.muntashirakon.adb.AdbStream;

// What the Python program calls on the phone instead of the adb command (see tvaccel/adb.py).
// One TV at a time: the one the program found.
public final class AdbBridge {
    private static Context context;
    private static String serial;

    private AdbBridge() {}

    static void init(Context c) { context = c.getApplicationContext(); }

    private static TvAdbManager manager() throws Exception { return TvAdbManager.get(context); }

    // "device", or "unauthorized" while the TV has not allowed this phone yet.
    public static synchronized String connect(String host, int port, int timeoutMs) throws Exception {
        TvAdbManager m = manager();
        String want = host + ":" + port;
        if (m.isConnected() && want.equals(serial)) return "device";
        if (m.isConnected()) m.disconnect();
        // Wait as long as "Allow debugging?" may be on the TV (the program gives up after 5 minutes too):
        // a shorter wait made the phone connect again and the TV ask a second time.
        m.setTimeout(Math.max(timeoutMs, 300_000), TimeUnit.MILLISECONDS);
        boolean ok = m.connect(host, port);
        serial = ok ? want : null;
        return ok ? "device" : "unauthorized";
    }

    public static synchronized String connectedSerial() throws Exception {
        return manager().isConnected() ? serial : null;
    }

    public static synchronized void disconnect() throws Exception {
        if (manager().isConnected()) manager().disconnect();
        serial = null;
    }

    public static String shell(String command, int timeoutMs) throws Exception {
        try (AdbStream s = manager().openStream("shell:" + command)) {
            return readAll(s.openInputStream());
        }
    }

    // cmd package install -S <size>, with the APK streamed in: no file copy to the TV needed.
    public static String install(String path, int timeoutMs) throws Exception {
        File f = new File(path);
        try (AdbStream s = manager().openStream("exec:cmd package install -S " + f.length())) {
            try (OutputStream out = s.openOutputStream(); InputStream in = new FileInputStream(f)) {
                byte[] buf = new byte[64 * 1024];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                out.flush();
            }
            return readAll(s.openInputStream());
        }
    }

    public static void reboot() throws Exception {
        try (AdbStream s = manager().openStream("reboot:")) {
            readAll(s.openInputStream());
        } catch (Exception ignored) {
            // the connection drops as the TV goes down
        }
        serial = null;
    }

    private static String readAll(InputStream in) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[16 * 1024];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        return out.toString(StandardCharsets.UTF_8.name());
    }
}
