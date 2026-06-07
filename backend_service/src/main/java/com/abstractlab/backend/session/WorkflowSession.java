package com.abstractlab.backend.session;

import com.abstractlab.backend.mode.Mode;

import org.springframework.stereotype.Component;

@Component
public class WorkflowSession {

    private Mode activeMode;
    private String sessionId;
    private boolean activeListening = false;

    public Mode getActiveMode() {

        return activeMode;
    }

    public void setActiveMode(
            Mode activeMode
    ) {

        this.activeMode =
                activeMode;
    }

    public boolean isActiveListening() {

        return activeListening;
    }

    public void setActiveListening(
            boolean activeListening
    ) {

        this.activeListening =
                activeListening;
    }

    public boolean hasActiveMode() {

        return activeMode != null;
    }

    public String getSessionId() {
    return sessionId;
    }

    public void setSessionId(
            String sessionId
    ) {
        this.sessionId = sessionId;
    }

    public void reset() {

        activeListening = false;

    }

    public void clear() {
        sessionId = null;
        activeMode = null;
        activeListening = false;
    }
}