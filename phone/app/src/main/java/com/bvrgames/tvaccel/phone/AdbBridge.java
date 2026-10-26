package com.bvrgames.tvaccel.phone;

import android.content.Context;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;

import io.github.muntashirakon.adb.AdbStream;

// What the Python program calls on the phone instead of the adb command (see tvaccel/adb.py).
// One TV at a time: the one the program found.
public final class AdbBridge {
    private static Context context;
    private static String serial;

    private static final ExecutorService calls = Executors.newCachedThreadPool();

    private AdbBridge() {}

    private interface Work { String run(AdbStream s) throws Exception; }

    // Every command gets a time limit, opening its stream included: a TV that stops answering
    // (or a connection that silently died when the phone changed networks) must not hang the
    // program. On timeout the stream is closed, which also ends the waiting read.
    private static String timed(String destination, Work work, int timeoutMs) throws Exception {
        AtomicReference<AdbStream> opened = new AtomicReference<>();
        Future<String> f = calls.submit(() -> {
            try (AdbStream s = manager().openStream(destination)) {
                opened.set(s);
                return work.run(s);
            }
        });
        try {
            return f.get(timeoutMs, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            AdbStream s = opened.get();
            if (s != null) try { s.close(); } catch (Exception ignored) { }
            f.cancel(true);
            throw new TimeoutException("the TV did not answer in " + timeoutMs / 1000 + " s");
        } catch (ExecutionException e) {
            Throwable cause = e.getCause();
            throw cause instanceof Exception ? (Exception) cause : e;
        }
    }

    static void init(Context c) { context = c.getApplicationContext(); }

    private static TvAdbManager manager() throws Exception { return TvAdbManager.get(context); }

    // "device", or "unauthorized" while the TV has not allowed this phone yet.
    public static synchronized String connect(String host, int port, int timeoutMs) throws Exception {
        TvAdbManager m = manager();
        String want = host + ":" + port;
        if (m.isConnected() && want.equals(serial)) return "device";
        if (m.isConnected()) m.disconnect();
        // libadb opens its socket with no time limit: an address nobody answers on (the TV moved
        // to another network) would hang for minutes. Knock first, briefly.
        try (Socket probe = new Socket()) {
            probe.connect(new InetSocketAddress(host, port), 3000);
        } catch (java.io.IOException e) {
            serial = null;
            throw new java.io.IOException("the TV does not answer at " + want + ": " + e.getMessage());
        }
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
        return timed("shell:" + command, AdbBridge::readAll, timeoutMs);
    }

    // cmd package install -S <size>, with the APK streamed in: no file copy to the TV needed.
    public static String install(String path, int timeoutMs) throws Exception {
        File f = new File(path);
        return timed("exec:cmd package install -S " + f.length(), s -> {
            try (OutputStream out = s.openOutputStream(); InputStream in = new FileInputStream(f)) {
                byte[] buf = new byte[64 * 1024];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                out.flush();
            }
            return readAll(s);
        }, timeoutMs);
    }

    public static void reboot() throws Exception {
        try {
            timed("reboot:", AdbBridge::readAll, 10_000);
        } catch (Exception ignored) {
            // the connection drops as the TV goes down
        }
        serial = null;
    }

    // The phone's own IPv4 addresses on local networks, one per line: Wi-Fi, or its hotspot when
    // the TV is connected to the phone. Mobile data is left out (no TV there).
    public static String localAddresses() throws Exception {
        StringBuilder out = new StringBuilder();
        for (NetworkInterface i : Collections.list(NetworkInterface.getNetworkInterfaces())) {
            String name = i.getName();
            if (!i.isUp() || i.isLoopback() || name.matches("(rmnet|ccmni|pdp|clat|v4-|seth_lte|dummy|tun).*")) continue;
            for (InetAddress a : Collections.list(i.getInetAddresses())) {
                if (a instanceof Inet4Address && a.isSiteLocalAddress()) out.append(a.getHostAddress()).append('\n');
            }
        }
        return out.toString();
    }

    // Reads the whole answer. Not with a plain blocking read: in libadb 3.1.1, when the TV closes a
    // stream while part of the answer is still unread, the stream is only marked "pending close";
    // after the rest is read, read() waits forever (it never checks that mark), so big answers
    // (dumpsys) hung now and then. Here we read only what is there and stop once the stream is
    // closed or pending close and empty. And a closed stream ends with "Stream closed." rather
    // than -1, so that is the normal end too.
    private static String readAll(AdbStream s) throws Exception {
        InputStream in = s.openInputStream();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[64 * 1024];
        while (true) {
            int ready;
            try {
                ready = s.available();
            } catch (java.io.IOException closed) {  // closed: take what is left in its buffer, then stop
                try {
                    int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                } catch (java.io.IOException end) { /* nothing left */ }
                break;
            }
            if (ready > 0) {
                int n = in.read(buf, 0, Math.min(ready, buf.length));
                if (n > 0) out.write(buf, 0, n);
            } else if (PENDING_CLOSE.getBoolean(s)) {
                break;  // closed by the TV and all read: nothing comes after a close
            } else if (!s.isClosed()) {  // (closed: the next available() says so and ends the loop)
                Thread.sleep(5);
            }
        }
        return out.toString(StandardCharsets.UTF_8.name());
    }

    private static final java.lang.reflect.Field PENDING_CLOSE;
    static {
        try {
            PENDING_CLOSE = AdbStream.class.getDeclaredField("mPendingClose");
            PENDING_CLOSE.setAccessible(true);
        } catch (NoSuchFieldException e) {
            throw new IllegalStateException("libadb changed: see readAll", e);
        }
    }
}
