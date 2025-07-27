package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;

public class SpoonClassLoader {
    private static SpoonClassLoader instance;

    private ClassLoader classLoader;

    private SpoonClassLoader() {
        this.classLoader = this.getClass().getClassLoader();
    }

    public static SpoonClassLoader getInstance() {
        if (instance == null) {
            instance = new SpoonClassLoader();
        }
        return instance;
    }

    public void setClassLoader(String[] classpath) {
        try {
            URL[] urls = new URL[classpath.length];
            for (int i = 0; i < classpath.length; i++) {
                urls[i] = new File(classpath[i]).toURI().toURL();
            }
            this.classLoader = new URLClassLoader(urls, this.getClass().getClassLoader());
        } catch (Exception e) {
            System.err.println("Error while creating classpath: " + e.getMessage());
            this.classLoader = this.getClass().getClassLoader();
        }
    }

    public ClassLoader getClassLoader() {
        return this.classLoader;
    }
}
