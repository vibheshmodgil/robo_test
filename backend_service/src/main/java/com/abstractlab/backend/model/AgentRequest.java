package com.abstractlab.backend.model;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AgentRequest {

    @JsonProperty("user_input")
    private String user_input;

    private String mode;

    private String method;

    private String phase;

    private List<String> description;

    public String getUserInput() {
        return user_input;
    }

    public void setUserInput(
            String user_input
    ) {
        this.user_input = user_input;
    }

    public String getMode() {
        return mode;
    }

    public void setMode(
            String mode
    ) {
        this.mode = mode;
    }

    public String getMethod() {
        return method;
    }

    public void setMethod(
            String method
    ) {
        this.method = method;
    }

    public String getPhase() {
        return phase;
    }

    public void setPhase(
            String phase
    ) {
        this.phase = phase;
    }

    public List<String> getDescription() {
        return description;
    }

    public void setDescription(
            List<String> description
    ) {
        this.description = description;
    }
}