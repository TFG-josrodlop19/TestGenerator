package com.example;

import java.io.Serializable;

public class User implements Serializable {
    private static final long serialVersionUID = 1L;
    public int id;
    public String name;

    public User(int id, String name) {
        this.id = id;
        this.name = name;
    }
}