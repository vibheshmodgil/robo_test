package com.abstractlab.backend.model;

import java.util.List;

public class AgentResponse {

    private String mode;

    private String method;

    private String phase;

    private String reply;

    private List<String> description;

    private Boolean complete;

    public String getMode() {
        return mode;
    }

    public void setMode(
            String mode
    ) {
        this.mode = mode;
    }

    public String getReply() {
        return reply;
    }

    public void setReply(
            String reply
    ) {
        this.reply = reply;
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

    public Boolean getComplete() {
        return complete;
    }

    public void setComplete(
            Boolean complete
    ) {
        this.complete = complete;
    }


}