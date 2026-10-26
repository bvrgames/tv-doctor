package com.bvrgames.tvaccel.phone;

import android.content.Context;
import android.os.Build;

import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder;
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.math.BigInteger;
import java.nio.file.Files;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Date;

import io.github.muntashirakon.adb.AbsAdbConnectionManager;

// The phone's adb identity: one RSA key, made on first run and kept in the app's files, so the
// TV's "Always allow from this device" is asked only once.
final class TvAdbManager extends AbsAdbConnectionManager {
    private static TvAdbManager instance;
    private final PrivateKey privateKey;
    private final Certificate certificate;

    static synchronized TvAdbManager get(Context c) throws Exception {
        if (instance == null) instance = new TvAdbManager(c);
        return instance;
    }

    private TvAdbManager(Context c) throws Exception {
        setApi(Build.VERSION.SDK_INT);
        File keyFile = new File(c.getFilesDir(), "adb.key"), certFile = new File(c.getFilesDir(), "adb.crt");
        if (keyFile.exists() && certFile.exists()) {
            privateKey = KeyFactory.getInstance("RSA")
                    .generatePrivate(new PKCS8EncodedKeySpec(Files.readAllBytes(keyFile.toPath())));
            certificate = CertificateFactory.getInstance("X.509")
                    .generateCertificate(new ByteArrayInputStream(Files.readAllBytes(certFile.toPath())));
            return;
        }
        KeyPairGenerator gen = KeyPairGenerator.getInstance("RSA");
        gen.initialize(2048);
        KeyPair pair = gen.generateKeyPair();
        long now = System.currentTimeMillis();
        X500Name name = new X500Name("CN=TV Doctor");
        JcaX509v3CertificateBuilder builder = new JcaX509v3CertificateBuilder(name, BigInteger.valueOf(now),
                new Date(now), new Date(now + 20L * 365 * 86_400_000L), name, pair.getPublic());
        certificate = new JcaX509CertificateConverter().getCertificate(
                builder.build(new JcaContentSignerBuilder("SHA256withRSA").build(pair.getPrivate())));
        privateKey = pair.getPrivate();
        Files.write(keyFile.toPath(), privateKey.getEncoded());
        Files.write(certFile.toPath(), certificate.getEncoded());
    }

    @Override protected PrivateKey getPrivateKey() { return privateKey; }
    @Override protected Certificate getCertificate() { return certificate; }
    @Override protected String getDeviceName() { return "TV Doctor"; }
}
