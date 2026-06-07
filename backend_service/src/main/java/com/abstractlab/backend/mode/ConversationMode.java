package com.abstractlab.backend.mode;

import com.abstractlab.backend.client.AudioClient;
import com.abstractlab.backend.client.LocalAgentClient;
import com.abstractlab.backend.client.SpeakerClient;
import com.abstractlab.backend.client.VisionClient;
import com.abstractlab.backend.model.AgentRequest;
import com.abstractlab.backend.model.AgentResponse;

import org.springframework.stereotype.Component;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Set;


@Component
public class ConversationMode implements Mode {

    private final SpeakerClient speakerClient;
    private final AudioClient audioClient;
    private final LocalAgentClient localAgentClient;
    private final VisionClient visionClient;

    private boolean complete = false;

    // Lightweight rolling context (AgentRequest has no history field).
    private final Deque<String> history = new ArrayDeque<>();
    private static final int MAX_HISTORY = 12;

    private static final Set<String> EXIT_WORDS = Set.of(
            "stop", "cancel", "exit", "quit", "goodbye", "bye"
    );
    private static final Set<String> EXIT_PHRASES = Set.of(
            "never mind", "nevermind", "that is all", "thats all", "done"
    );

    public ConversationMode(
            SpeakerClient speakerClient,
            AudioClient audioClient,
            LocalAgentClient localAgentClient,
            VisionClient visionClient
    ) {
        this.speakerClient = speakerClient;
        this.audioClient = audioClient;
        this.localAgentClient = localAgentClient;
        this.visionClient = visionClient;
    }

    public void start(String userInput, String firstReply) {

        complete = false;
        history.clear();

        if (userInput != null && !userInput.isBlank()) {
            remember("User", userInput.trim());
        }

        String reply = (firstReply == null || firstReply.isBlank())
                ? "Sure, what would you like to talk about?"
                : firstReply;

        remember("Assistant", reply);
        showPanel(reply);            // display what Shiv says
        speakAndContinue(reply);
    }

    @Override
    public void handle(String command) {

        if (command == null) {
            return;
        }

        command = command.trim();

        if (command.isBlank()) {
            return;
        }

        if (isExit(command)) {
            showPanel("Okay, talk to you later.");
            speakAndReturnPassive("Okay, talk to you later.");
            hidePanel();             // back to the base "Hi, I am Shiv" panel
            complete = true;
            return;
        }

        remember("User", command);

        String reply = chat();

        if (reply == null || reply.isBlank()) {
            reply = "Sorry, I didn't catch that.";
        }

        remember("Assistant", reply);
        showPanel(reply);            // display what Shiv says
        speakAndContinue(reply);
    }

    @Override
    public boolean isComplete() {
        return complete;
    }

    // --- conversation helpers ------------------------------------------

    private String chat() {
        AgentRequest request = new AgentRequest();
        request.setPhase("CHAT");
        request.setUserInput(buildTranscript());

        AgentResponse response = localAgentClient.processInventory(request);
        return response == null ? null : response.getReply();
    }

    private void remember(String role, String text) {
        history.addLast(role + ": " + text);
        while (history.size() > MAX_HISTORY) {
            history.removeFirst();
        }
    }

    private String buildTranscript() {
        StringBuilder sb = new StringBuilder("Conversation so far:\n");
        for (String line : history) {
            sb.append(line).append("\n");
        }
        sb.append("\nReply to the last user message.");
        return sb.toString();
    }

    private boolean isExit(String command) {
        String c = command.toLowerCase()
                .replaceAll("[^a-z ]", " ")
                .trim()
                .replaceAll(" +", " ");

        if (EXIT_PHRASES.contains(c)) {
            return true;
        }
        for (String token : c.split(" ")) {
            if (EXIT_WORDS.contains(token)) {
                return true;
            }
        }
        return false;
    }

    // --- vision (same single foreground panel inventory uses) ----------

    private void showPanel(String reply) {
        try {
            visionClient.showPanel("SHIV", reply);
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    private void hidePanel() {
        try {
            visionClient.closeActivePanel();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    // --- speech helpers (each mutes the mic while the speaker is talking) ---

    private void speakAndContinue(String text) {
        audioClient.pauseListening();
        try {
            speakerClient.speakAndWait(text);
            audioClient.startFreshWorkflowListening();
        } finally {
            audioClient.resumeListening();
        }
    }

    private void speakAndReturnPassive(String text) {
        audioClient.pauseListening();
        try {
            speakerClient.speakAndWait(text);
            audioClient.enablePassiveListening();
        } finally {
            audioClient.resumeListening();
        }
    }
}