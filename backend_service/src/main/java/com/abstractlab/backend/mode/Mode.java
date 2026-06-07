package com.abstractlab.backend.mode;

public interface Mode {


    void handle(
            String command 
    );

    void start( String method,String getReply);

    boolean isComplete();
}